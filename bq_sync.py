#!/usr/bin/env python
"""Sync a BQ Studio notebook with a local .ipynb file.

Reads configuration from a .env file in the same directory.
See .env.example for required variables.

Usage:
    python bq_sync.py pull   # download notebook from BQ Studio
    python bq_sync.py push   # upload local notebook to BQ Studio
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path


def _load_env(path=None):
    """Load KEY=VALUE pairs from a .env file into os.environ."""
    if path is None:
        path = Path(__file__).parent / ".env"
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())
    except FileNotFoundError:
        pass


_load_env()


def _cfg(key):
    """Read a required config value from the environment."""
    value = os.environ.get(key)
    if not value:
        print(f"Error: {key} is not set. Copy .env.example to .env and fill it in.", file=sys.stderr)
        sys.exit(1)
    return value


PROJECT = _cfg("GCP_PROJECT")
LOCATION = _cfg("GCP_LOCATION")
REPO_ID = _cfg("BQ_NOTEBOOK_REPO_ID")
NOTEBOOK = _cfg("BQ_NOTEBOOK_FILE")
AUTHOR_NAME = _cfg("SYNC_AUTHOR_NAME")
AUTHOR_EMAIL = _cfg("SYNC_AUTHOR_EMAIL")

REPO = f"projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_ID}"
API = f"https://dataform.googleapis.com/v1beta1/{REPO}"


def _get_token():
    result = subprocess.run(
        "gcloud auth print-access-token",
        capture_output=True, text=True, check=True, shell=True,
    )
    return result.stdout.strip()


def _api_request(url, method="GET", data=None):
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    else:
        body = None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _clean_notebook(raw_bytes):
    """Strip BQ Studio artifacts that break GitHub's notebook renderer."""
    nb = json.loads(raw_bytes)
    # BQ Studio stores widget state in a non-standard format that nbformat
    # rejects (missing top-level 'state' key). These are runtime artifacts
    # (interactive table/chart viewers) that regenerate on cell execution.
    nb.get("metadata", {}).pop("widgets", None)
    return json.dumps(nb, ensure_ascii=False, indent=1).encode("utf-8")


def pull():
    url = f"{API}:readFile?path=content.ipynb"
    result = _api_request(url)
    contents = _clean_notebook(base64.b64decode(result["contents"]))
    with open(NOTEBOOK, "wb") as f:
        f.write(contents)
    print(f"Pulled {NOTEBOOK} from BQ Studio ({len(contents):,} bytes)")


def push():
    with open(NOTEBOOK, "rb") as f:
        contents = base64.b64encode(f.read()).decode()
    body = {
        "commitMetadata": {
            "author": {
                "name": AUTHOR_NAME,
                "emailAddress": AUTHOR_EMAIL,
            },
            "commitMessage": "sync from local",
        },
        "fileOperations": {
            "content.ipynb": {
                "writeFile": {"contents": contents},
            },
        },
    }
    _api_request(f"{API}:commit", method="POST", data=body)
    print(f"Pushed {NOTEBOOK} to BQ Studio")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync notebook with BQ Studio")
    parser.add_argument("action", choices=["pull", "push"])
    args = parser.parse_args()
    {"pull": pull, "push": push}[args.action]()
