# Webhook-Server

Webhook Server is a lightweight Flask (python) server to listen for incoming webhooks and process them based on predefined rules.

It aims to run as a systemd service on a Linux server, listening for incoming webhooks from platforms like GitHub, GitLab, or Bitbucket. Upon receiving a webhook, it triggers a bash script to handle the event. 

Unfortuantely depending on script, user has to be priveleged to run certain commands like restarting services, pulling from git repos etc.

```
Github Webhook ----> Webhook Server ----> Bash Script
```

## Installation

```bash
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
WEBHOOK_SECRET=your-github-webhook-secret
SCRIPTS_DIR=./scripts
PORT=9000
LOG_DIR=/var/log/webhook-server
```

## Usage

```bash
# Development
python src/main.py

# Production with gunicorn
gunicorn -w 4 -b 0.0.0.0:9000 src.main:app
```

## Endpoints

- `POST /webhook/<project>` - Execute a command for a specific project
- `GET /health` - Health check endpoint

### Scripts Directory Structure

```
scripts/
├── project.sh      # Called for /webhook/<project>
```

Each script receives the project name as the first argument (`$1`).

## Logging

Logs are written to:
- **Console**: INFO level and above
- **File**: `$LOG_DIR/webhook-server.log` with DEBUG level, 10MB rotation, 30-day retention, gzip compression

## Systemd Service Setup

1. Copy the project to `/opt/webhook-server`:
   ```bash
   sudo cp -r . /opt/webhook-server
   cd /opt/webhook-server
   ```

2. Create virtual environment and install dependencies:
   ```bash
   sudo python3 -m venv .venv
   sudo .venv/bin/pip install -e .
   ```

3. Create log directory:
   ```bash
   sudo mkdir -p /var/log/webhook-server
   sudo chown www-data:www-data /var/log/webhook-server
   ```

4. Configure environment:
   ```bash
   sudo cp .env.example .env
   sudo nano .env  # Edit with your values
   ```

5. Install/Update and Enable the service:
   ```bash
   sudo cp webhook-server.service /etc/systemd/system/ # requires to edit user and filepaths
   sudo systemctl daemon-reload
   sudo systemctl enable webhook-server
   sudo systemctl start webhook-server
   ```

6. Check status:
   ```bash
   sudo systemctl status webhook-server
   sudo journalctl -u webhook-server -f
   ```

## GitHub Webhook Setup

1. Go to your GitHub repo → Settings → Webhooks → Add webhook
2. Set Payload URL to `https://your-server.com/webhook/<project-name>` (e.g., `https://server.giraycoskun.dev/webhook/my-app`)
3. Set Content type to `application/json`
4. Set Secret to match your `WEBHOOK_SECRET`
5. Select events to trigger the webhook

## Sample

```bash
# Example cURL to test webhook endpoint
curl -X POST "https://webhook.giraycoskun.dev/server-giraycoskun-dev" \
     -H "Accept: */*" \
     -H "Content-Type: application/json" \
     -H "User-Agent: GitHub-Hookshot/9082f66" \
     -H "X-GitHub-Delivery: bb6f8208-fd6e-11f0-9417-29c285ee9596" \
     -H "X-GitHub-Event: push" \
     -H "X-GitHub-Hook-ID: 582933851" \
     -H "X-GitHub-Hook-Installation-Target-ID: 1080613886" \
     -H "X-GitHub-Hook-Installation-Target-Type: repository" \
     -H "X-Hub-Signature: sha1=e4828872c922807d6e1dbc9f7e8275eff220339a" \
     -H "X-Hub-Signature-256: sha256=fedd1145dac9d566bdf83b1843a8d3d64759c3313f211b47ca025e8e99cb6977" \
     -d '{"ref": "refs/heads/main", "repository": {"name": "f1-board", "full_name": "giraycoskun/f1-board"}}'
```
