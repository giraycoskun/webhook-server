# Webhook-Server

Webhook Server is a lightweight Flask (python) server to listen for incoming webhooks and process them based on predefined rules.

It aims to run as a systemd service on a Linux server, listening for incoming webhooks from platforms like GitHub, GitLab, or Bitbucket. Upon receiving a webhook, it triggers a bash script to handle the event. 

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

- `POST /webhook/<command>/<project>` - Execute a command for a specific project
- `GET /health` - Health check endpoint

### Allowed Commands

The following commands are supported (each requires a corresponding `<command>.sh` script in `SCRIPTS_DIR`):

- `deploy` - Deploy the project
- `restart` - Restart the project service
- `stop` - Stop the project service
- `start` - Start the project service
- `update` - Update the project

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

5. Install and enable the service:
   ```bash
   sudo cp webhook-server.service /etc/systemd/system/
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
