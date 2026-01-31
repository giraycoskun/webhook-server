import hashlib
import hmac
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from loguru import logger

load_dotenv()

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

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
SCRIPTS_DIR = Path(os.getenv("SCRIPTS_DIR", "./scripts"))
PORT = int(os.getenv("PORT", "9000"))


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

        for line in process.stdout:
            logger.info(f"[{project}] {line.rstrip()}")

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
    logger.info(f"Script started in background thread")

    return jsonify({"status": "OK", "project": project}), 200


@app.route("/health", methods=["GET"])
def health():
    from datetime import datetime, timezone
    response = {"status": "OK", "timestamp": datetime.now(timezone.utc).isoformat()}
    logger.info("Health check request: " + str(response))
    return jsonify(
        response
    )


def main():
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not set - signature verification disabled")

    logger.info(f"Starting webhook server on port {PORT}")
    logger.info(f"Scripts directory: {SCRIPTS_DIR}")
    logger.info(f"Log directory: {LOG_DIR}")
    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    main()
