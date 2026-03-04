#!/bin/bash
set -Eeuo pipefail

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

on_error() {
    local exit_code="$1"
    local line_no="$2"
    log "ERROR exit=${exit_code} line=${line_no} cmd=${BASH_COMMAND}"
    exit "${exit_code}"
}

trap 'on_error $? $LINENO' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    # shellcheck disable=SC1090
    source "${PROJECT_ROOT}/.env"
fi

REPO_OWNER="${REPO_OWNER:-giraycoskun}"
REPO_NAME="${REPO_NAME:-cv}"
REPO_BRANCH="${REPO_BRANCH:-main}"
NGINX_GROUP="${NGINX_GROUP:-www-data}"

# Where dated CV files are stored.
CV_STORE_DIR="${CV_STORE_DIR:-/media/images/cv/pdf}"
# Stable file path used by Nginx (serve this path forever).
SERVE_FILE="${SERVE_FILE:-/media/images/cv.pdf}"

GITHUB_API_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/git/trees/${REPO_BRANCH}?recursive=1"

curl_github() {
    local url="$1"

    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        curl -fsSL \
            -H "Accept: application/vnd.github+json" \
            -H "Authorization: Bearer ${GITHUB_TOKEN}" \
            "${url}"
    else
        curl -fsSL \
            -H "Accept: application/vnd.github+json" \
            "${url}"
    fi
}

echo "--- Finding latest CV in ${REPO_OWNER}/${REPO_NAME} (${REPO_BRANCH}) ---"
log "GitHub API URL: ${GITHUB_API_URL}"
tree_json="$(curl_github "${GITHUB_API_URL}")"

latest_file="$(
    printf '%s' "${tree_json}" \
        | grep -Eo '"path"[[:space:]]*:[[:space:]]*"cv_long_[0-9]{4}-[0-9]{2}-[0-9]{2}\.pdf"' \
        | sed -E 's/^"path"[[:space:]]*:[[:space:]]*"([^"]*)"$/\1/' \
        | sort \
        | tail -n 1 || true
)"

if [[ -z "${latest_file}" ]]; then
    log "No file matching cv_long_YYYY-MM-DD.pdf was found in ${REPO_OWNER}/${REPO_NAME}."
    log "Checked URL: ${GITHUB_API_URL}"
    log "First path entries from API response (if any):"
    printf '%s' "${tree_json}" \
        | grep -Eo '"path"[[:space:]]*:[[:space:]]*"[^"]+"' \
        | head -n 20 || true
    exit 1
fi

log "Latest file resolved: ${latest_file}"
mkdir -p "${CV_STORE_DIR}"

target_file="${CV_STORE_DIR}/${latest_file}"
raw_url="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${REPO_BRANCH}/${latest_file}"
log "Target file path: ${target_file}"
log "Raw download URL: ${raw_url}"

if [[ -f "${target_file}" ]]; then
    echo "--- ${latest_file} already exists locally ---"
else
    log "Downloading ${latest_file}"
    tmp_file="$(mktemp "${CV_STORE_DIR}/.${latest_file}.tmp.XXXXXX")"
    trap 'rm -f "${tmp_file}"' EXIT

    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        curl -fsSL \
            -H "Authorization: Bearer ${GITHUB_TOKEN}" \
            -o "${tmp_file}" \
            "${raw_url}"
    else
        curl -fsSL -o "${tmp_file}" "${raw_url}"
    fi

    if ! head -c 5 "${tmp_file}" | grep -q '^%PDF-'; then
        echo "Downloaded file is not a valid PDF header: ${raw_url}"
        exit 1
    fi

    mv "${tmp_file}" "${target_file}"
    trap - EXIT
fi

# Ensure Nginx can read the served PDF regardless of current umask.
chmod 0644 "${target_file}"
chgrp "${NGINX_GROUP}" "${target_file}" 2>/dev/null || true
log "Permissions ensured: mode=0644 group=${NGINX_GROUP} file=${target_file}"

mkdir -p "$(dirname "${SERVE_FILE}")"
ln -sfn "${target_file}" "${SERVE_FILE}"
log "Symlink updated: ${SERVE_FILE} -> ${target_file}"

echo "--- CV updated ---"
echo "Stored file : ${target_file}"
echo "Served file : ${SERVE_FILE} -> ${target_file}"
