import hashlib
import hmac
import os
import subprocess
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, jsonify, redirect, request, url_for
from flask_cors import CORS
from loguru import logger
from werkzeug.middleware.proxy_fix import ProxyFix

from app import version

load_dotenv()

PASS = os.getenv("PASS")

LOG_DIR = Path(os.getenv("LOG_DIR", "./logs"))

try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    LOG_DIR = Path("./logs")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="INFO",
)
logger.add(
    LOG_DIR / "webhook-server.log",
    rotation="5 MB",
    retention="30 days",
    compression="gz",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="DEBUG",
)
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure CORS for Swagger UI - only allow specific origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:9000").split(",")
CORS(
    app,
    resources={
        r"/*": {
            "origins": ALLOWED_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-Hub-Signature-256", "X-Password"],
        }
    },
)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
SCRIPTS_DIR = Path(os.getenv("SCRIPTS_DIR", "./scripts"))
PORT = int(os.getenv("PORT", "9000"))

# Configure Swagger using Flasgger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs",
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Webhook Server API",
        "description": "A Flask-based webhook server for triggering build scripts via GitHub webhooks or manual triggers",
        "version": version,
        "contact": {
            "name": "API Support"
        }
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "GitHubSignature": {
            "type": "apiKey",
            "name": "X-Hub-Signature-256",
            "in": "header",
            "description": "GitHub webhook signature for verifying payload authenticity using HMAC-SHA256"
        },
        "Password": {
            "type": "apiKey",
            "name": "X-Password",
            "in": "header",
            "description": "Password for manual trigger authentication"
        }
    },
    "tags": [
        {
            "name": "System",
            "description": "System health and status endpoints"
        },
        {
            "name": "Webhooks",
            "description": "GitHub webhook integration endpoints"
        },
        {
            "name": "Manual Triggers",
            "description": "Password-protected manual trigger endpoints"
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)


def run_script_with_logging(script_path: Path, project: str):
    """Run script and log output to loguru."""
    try:
        logger.info(f"[{project}] Starting script: {script_path}")

        process = subprocess.Popen(
            [str(script_path), project],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=SCRIPTS_DIR,
            text=True,
        )

        if process.stdout is not None:
            for line in process.stdout:
                logger.info(f"[{project}] {line.rstrip()}")
        else:
            logger.error(f"[{project}] No stdout to read from the process")

        process.wait()

        if process.returncode == 0:
            logger.info(f"[{project}] Script completed successfully (exit code: 0)")
        else:
            logger.error(f"[{project}] Script failed with exit code: {process.returncode}")

    except Exception as e:
        logger.error(f"[{project}] Error running script: {e}")


def verify_github_signature(payload: bytes, signature_header: str | None) -> bool:
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not configured - skipping verification")
        return True

    if not signature_header:
        logger.warning("No signature header found")
        return False

    expected_signature = (
        "sha256="
        + hmac.new(
            WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(expected_signature, signature_header)


@app.route("/<project>", methods=["POST"])
def webhook(project: str):
    """
    GitHub Webhook Endpoint
    ---
    tags:
      - Webhooks
    summary: Receive GitHub webhook events
    description: Receive GitHub webhook events and trigger corresponding build scripts. The webhook payload is verified using HMAC-SHA256 signature.
    parameters:
      - name: project
        in: path
        type: string
        required: true
        description: Project name (must have corresponding .sh script in scripts directory)
        example: myproject
      - name: X-Hub-Signature-256
        in: header
        type: string
        required: true
        description: GitHub webhook HMAC-SHA256 signature
        example: sha256=5c3b8f9e2a1d4c7b6a8f3e2d1c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b
      - name: body
        in: body
        required: true
        description: GitHub webhook payload
        schema:
          type: object
          properties:
            ref:
              type: string
              example: refs/heads/main
            repository:
              type: object
              properties:
                name:
                  type: string
                  example: myproject
    security:
      - GitHubSignature: []
    responses:
      200:
        description: Webhook received and script triggered
        schema:
          type: object
          properties:
            status:
              type: string
              example: OK
            project:
              type: string
              example: myproject
      403:
        description: Invalid signature - webhook verification failed
        schema:
          type: object
          properties:
            error:
              type: string
              example: Invalid signature
      500:
        description: Script not found in scripts directory
        schema:
          type: object
          properties:
            error:
              type: string
              example: Script not found myproject.sh
    """
    logger.info(f"Received webhook - project: {project}")

    payload = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_github_signature(payload, signature):
        logger.warning("Invalid signature - rejecting request")
        return jsonify({"error": "Invalid signature"}), 403

    script_path = SCRIPTS_DIR / f"{project}.sh"
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return jsonify({"error": f"Script not found: {project}.sh"}), 500

    logger.info(f"Executing {script_path} for project {project}")

    thread = threading.Thread(
        target=run_script_with_logging,
        args=(script_path, project),
        daemon=True,
    )
    thread.start()
    logger.info("Script started in background thread")

    return jsonify({"status": "OK", "project": project}), 200


@app.route("/manual/<project>", methods=["POST"])
def manual_trigger(project: str):
    """
    Manual Trigger Endpoint
    ---
    tags:
      - Manual Triggers
    summary: Manually trigger a build script
    description: Manually trigger a build script with password authentication. Password can be provided via X-Password header (recommended) or as a query parameter.
    parameters:
      - name: project
        in: path
        type: string
        required: true
        description: Project name (must have corresponding .sh script in scripts directory)
        example: myproject
      - name: X-Password
        in: header
        type: string
        required: false
        description: Authentication password (recommended over query parameter for security)
        example: mySecretPassword
      - name: password
        in: query
        type: string
        required: false
        description: Authentication password (can also be provided via X-Password header)
        example: mySecretPassword
    security:
      - Password: []
    responses:
      200:
        description: Script triggered successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: OK
            project:
              type: string
              example: myproject
            trigger:
              type: string
              example: manual
      401:
        description: Invalid password or password not provided
        schema:
          type: object
          properties:
            error:
              type: string
              example: Invalid password
      404:
        description: Script not found in scripts directory
        schema:
          type: object
          properties:
            error:
              type: string
              example: Script not found myproject.sh
      500:
        description: Server configuration error - PASS environment variable not set
        schema:
          type: object
          properties:
            error:
              type: string
              example: Server configuration error
    """
    logger.info(f"Manual trigger request - project: {project}")
    
    # Check password from header or query parameter
    password = request.headers.get("X-Password") or request.args.get("password")
    
    if not PASS:
        logger.error("PASS environment variable not configured")
        return jsonify({"error": "Server configuration error"}), 500
    
    if not password or password != PASS:
        logger.warning(f"Invalid password attempt for project: {project}")
        return jsonify({"error": "Invalid password"}), 401
    
    script_path = SCRIPTS_DIR / f"{project}.sh"
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return jsonify({"error": f"Script not found: {project}.sh"}), 404
    
    logger.info(f"Manual trigger: executing {script_path} for project {project}")
    
    thread = threading.Thread(
        target=run_script_with_logging,
        args=(script_path, project),
        daemon=True,
    )
    thread.start()
    logger.info("Script started in background thread (manual trigger)")
    
    return jsonify({"status": "OK", "project": project, "trigger": "manual"}), 200


@app.route("/health", methods=["GET"])
def health():
    """
    Health Check Endpoint
    ---
    tags:
      - System
    summary: Health Check
    description: Check the health status of the webhook server
    responses:
      200:
        description: Server is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: OK
            version:
              type: string
              example: 1.0.0
            timestamp:
              type: string
              format: date-time
              example: 2026-02-01T12:00:00.000Z
    """
    response = {
        "status": "OK",
        "version": version,
        "timestamp": datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S GMT"),
    }
    logger.info("Health check request: " + str(response))
    return jsonify(response)


@app.route("/")
def root():
    """
    Root Endpoint
    ---
    tags:
      - System
    summary: Root endpoint
    description: Redirects to the health check endpoint
    responses:
      302:
        description: Redirect to /health
    """
    return redirect(url_for("health"))


def main():
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not set - signature verification disabled")

    logger.info(f"Starting webhook server on port {PORT}")
    logger.info(f"Scripts directory: {SCRIPTS_DIR}")
    logger.info(f"Log directory: {LOG_DIR}")
    logger.info(f"API Documentation available at: http://localhost:{PORT}/docs")
    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    main()