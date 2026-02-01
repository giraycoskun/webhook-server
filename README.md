# Webhook-Server

Webhook Server is a lightweight Flask (python) server to listen for incoming webhooks and process them based on predefined rules.

This project is meant to be a personal project (shared as it might be useful example) to keep track of incoming webhooks and trigger custom bash scripts. It aims to run as a systemd service on a Linux server, listening for incoming webhooks from platforms like GitHub, GitLab, or Bitbucket. Upon receiving a webhook, it triggers a bash script to handle the event.  

Unfortuantely depending on script, user has to be priveleged to run certain commands like restarting services, pulling from git repos etc.

```
Github Webhook ----> Webhook Server ----> Bash Script
```

## Features

- ✅ GitHub webhook integration with HMAC signature verification
- ✅ Password-protected manual trigger endpoint
- ✅ **Interactive OpenAPI/Swagger documentation**
- ✅ Logging with loguru
- ✅ Background script execution
- ✅ Health check endpoint

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
uv run python -m app.main

# Production with gunicorn
gunicorn -w 4 -b 0.0.0.0:9000 src.main:app
```

## API Endpoints

### 1. Health Check
**GET** `/health`

Check server health and version.

```bash
curl http://localhost:9000/health
```

Response:
```json
{
  "status": "OK",
  "version": "1.0.0",
  "timestamp": "2026-02-01T12:00:00Z"
}
```

### 2. GitHub Webhook
**POST** `/{project}`

Receive GitHub webhook events (requires valid HMAC signature).

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d '{"ref": "refs/heads/main"}' \
  http://localhost:9000/myproject
```

### 3. Manual Trigger (Password Protected)
**POST** `/manual/{project}`

Manually trigger build scripts with password authentication.

#### Using Header (Recommended):
```bash
curl -X POST \
  -H "X-Password: your_password" \
  http://localhost:9000/manual/myproject
```

#### Using Query Parameter:
```bash
curl -X POST \
  "http://localhost:9000/manual/myproject?password=your_password"
```

Response:
```json
{
  "status": "OK",
  "project": "myproject",
  "trigger": "manual"
}
```

## Directory Structure

```
.
├── main.py                  # Main Flask application
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration (create this)
├── scripts/                 # Build scripts directory
│   ├── myproject.sh
│   └── another-project.sh
└── logs/                    # Log files (auto-created)
    └── webhook-server.log
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEBHOOK_SECRET` | No | None | GitHub webhook secret for HMAC verification |
| `PASS` | Yes* | None | Password for manual trigger endpoint |
| `SCRIPTS_DIR` | No | `./scripts` | Directory containing build scripts |
| `LOG_DIR` | No | `./logs` | Directory for log files |
| `PORT` | No | `9000` | Server port |

*Required if using the `/manual/{project}` endpoint


## Security Notes

### GitHub Webhooks
- Configure webhook secret in GitHub repository settings
- Set the same secret in your `WEBHOOK_SECRET` environment variable
- Requests without valid signatures are rejected with 403

### Manual Triggers
- Always use HTTPS in production
- Password is verified using constant-time comparison
- Use the `X-Password` header instead of query parameters (headers are less likely to be logged)
- Keep your `PASS` environment variable secret

## Logging

Logs are written to:
- Console (INFO level and above)
- File at `{LOG_DIR}/webhook-server.log` (DEBUG level)
  - Rotated at 5 MB
  - Retained for 30 days
  - Compressed with gzip

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

## Testing the API

### Using Swagger UI (Interactive)
1. Start the server
2. Open http://localhost:9000/docs
3. Click on any endpoint to expand it
4. Click "Try it out"
5. Fill in parameters and click "Execute"

### Using curl

Health check:
```bash
curl http://localhost:9000/health
```

Manual trigger:
```bash
curl -X POST \
  -H "X-Password: mypass123" \
  http://localhost:9000/manual/test-project
```

Get OpenAPI spec:
```bash
curl http://localhost:9000/openapi.json | jq
```

## License

MIT
