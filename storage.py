"""
Dhvaani - Persistent Storage Abstraction (Vercel Blob + Local)
==============================================================
Handles evidence & attachment storage:
- Vercel Blob storage when BLOB_READ_WRITE_TOKEN is configured.
- Local filesystem storage (with /tmp fallback for serverless) for local dev and testing.
"""

import os
import requests
from pathlib import Path
from typing import Optional, Tuple

BLOB_READ_WRITE_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN", "").strip()


def is_blob_configured() -> bool:
    """Check if Vercel Blob storage token is configured."""
    return bool(BLOB_READ_WRITE_TOKEN and (
        BLOB_READ_WRITE_TOKEN.startswith("vercel_blob_rw_") or
        len(BLOB_READ_WRITE_TOKEN) > 20
    ))


def upload_to_blob(filename: str, data: bytes, content_type: str) -> Optional[str]:
    """
    Upload a file to Vercel Blob Storage via REST API.
    Returns the public/accessible blob URL, or None if upload failed or token not set.
    """
    if not is_blob_configured():
        return None

    try:
        url = f"https://blob.vercel-storage.com/{filename}"
        headers = {
            "Authorization": f"Bearer {BLOB_READ_WRITE_TOKEN}",
            "x-api-version": "7",
            "Content-Type": content_type,
        }
        resp = requests.put(url, data=data, headers=headers, timeout=15)
        if resp.status_code in (200, 201):
            res_json = resp.json()
            return res_json.get("url")
        else:
            print(f"[Dhvaani] Vercel Blob upload failed with status {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"[Dhvaani] Vercel Blob upload exception: {e}")
        return None


def delete_from_blob(blob_url: str) -> bool:
    """
    Delete a file from Vercel Blob Storage by its URL.
    """
    if not is_blob_configured() or not blob_url:
        return False

    try:
        url = "https://blob.vercel-storage.com/delete"
        headers = {
            "Authorization": f"Bearer {BLOB_READ_WRITE_TOKEN}",
            "x-api-version": "7",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, json={"urls": [blob_url]}, headers=headers, timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        print(f"[Dhvaani] Vercel Blob delete exception: {e}")
        return False
