"""
Dhvaani - Database Abstraction Layer (Production + Local)
==========================================================
Dual-mode database:
- LOCAL:      SQLite (sqlite3)  — uses DHVAANI_DB_PATH or ./dhvaani.db
- PRODUCTION: PostgreSQL        — uses DATABASE_URL (Vercel Postgres)

Postgres is used when DATABASE_URL env var is set (Vercel deployment).
SQLite is used otherwise (local development / testing).

No secrets stored in database. No binary files in database.
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

DATABASE_URL = os.getenv("DATABASE_URL", "")
_use_postgres = bool(DATABASE_URL and DATABASE_URL.startswith("postgres"))

if _use_postgres:
    import psycopg2
    import psycopg2.extras
else:
    import sqlite3

DEFAULT_DB_PATH = Path(__file__).parent / "dhvaani.db"


# ──────────────────────────────────────────────
# CONNECTION HELPERS
# ──────────────────────────────────────────────

def get_db_path() -> Path:
    env_path = os.getenv("DHVAANI_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def get_connection(db_path=None):
    """Return a database connection (Postgres or SQLite)."""
    if _use_postgres:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        target = db_path or get_db_path()
        conn = sqlite3.connect(str(target), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


def _placeholder(n: int = 1) -> str:
    """Return the correct SQL placeholder for the current DB backend."""
    if _use_postgres:
        return "%s"
    return "?"


def _placeholders(n: int) -> str:
    ph = _placeholder()
    return ", ".join([ph] * n)


def _autoincrement() -> str:
    if _use_postgres:
        return "SERIAL PRIMARY KEY"
    return "INTEGER PRIMARY KEY AUTOINCREMENT"


# ──────────────────────────────────────────────
# SCHEMA INIT
# ──────────────────────────────────────────────

def init_db(db_path=None):
    """Create schema tables if they do not exist."""
    conn = get_connection(db_path)
    if _use_postgres:
        cursor = conn.cursor()
    else:
        cursor = conn.cursor()

    autoincrement = _autoincrement()

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS requests (
        id {autoincrement},
        tracking_id TEXT UNIQUE,
        grievance_id TEXT UNIQUE,
        service_id TEXT,
        issue TEXT,
        category TEXT,
        department TEXT,
        location TEXT,
        priority TEXT,
        description TEXT,
        language TEXT DEFAULT 'en',
        status TEXT DEFAULT 'draft',
        submission_status TEXT DEFAULT 'draft',
        submission_mode TEXT DEFAULT 'assisted_handoff',
        government_reference_id TEXT,
        government_status TEXT,
        official_portal TEXT,
        official_helpline TEXT,
        user_name TEXT,
        contact TEXT,
        created_at TEXT,
        confirmed_at TEXT,
        extra_data TEXT
    )
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id {autoincrement},
        timestamp TEXT,
        action TEXT,
        entity_id TEXT,
        details TEXT
    )
    """)

    # Attachment metadata table — binary files on disk/blob storage only
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS attachments (
        id {autoincrement},
        attachment_id TEXT UNIQUE NOT NULL,
        dhvaani_request_id TEXT,
        original_filename TEXT NOT NULL,
        stored_filename TEXT NOT NULL,
        content_type TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        blob_url TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # Ensure migration for existing tables
    try:
        if not _use_postgres:
            cursor.execute("PRAGMA table_info(attachments)")
            cols = [r[1] for r in cursor.fetchall()]
            if cols and "blob_url" not in cols:
                cursor.execute("ALTER TABLE attachments ADD COLUMN blob_url TEXT")
        else:
            cursor.execute("ALTER TABLE attachments ADD COLUMN IF NOT EXISTS blob_url TEXT")
    except Exception:
        pass

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# REQUESTS CRUD
# ──────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    if row is None:
        return None
    if isinstance(row, dict):
        return dict(row)
    return dict(row)


def save_or_update_request(data: Dict[str, Any], db_path=None):
    """Upsert a Dhvaani request record."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    gid = data.get("grievance_id") or data.get("id") or ""
    tid = data.get("tracking_id") or data.get("dhvaani_request_id")

    # Serialize any extra complex fields
    simple_keys = {
        "tracking_id", "grievance_id", "service_id", "issue", "category",
        "department", "location", "priority", "description", "language",
        "status", "submission_status", "submission_mode",
        "government_reference_id", "government_status",
        "official_portal", "official_helpline", "user_name", "contact",
        "created_at", "confirmed_at"
    }
    extra = {k: v for k, v in data.items() if k not in simple_keys and k != "id"}
    extra_json = json.dumps(extra, ensure_ascii=False) if extra else None

    ph = _placeholder()

    # Check existing
    cursor.execute(f"SELECT id FROM requests WHERE grievance_id = {ph}", (gid,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(f"""
            UPDATE requests SET
                tracking_id={ph}, service_id={ph}, issue={ph}, category={ph},
                department={ph}, location={ph}, priority={ph}, description={ph},
                language={ph}, status={ph}, submission_status={ph},
                submission_mode={ph}, government_reference_id={ph},
                government_status={ph}, official_portal={ph},
                official_helpline={ph}, user_name={ph}, contact={ph},
                created_at={ph}, confirmed_at={ph}, extra_data={ph}
            WHERE grievance_id={ph}
        """, (
            tid, data.get("service_id"), data.get("issue"), data.get("category"),
            data.get("department"), data.get("location"), data.get("priority"),
            data.get("description"), data.get("language", "en"),
            data.get("status", "draft"), data.get("submission_status", "draft"),
            data.get("submission_mode", "assisted_handoff"),
            data.get("government_reference_id"), data.get("government_status"),
            data.get("official_portal"), data.get("official_helpline"),
            data.get("user_name"), data.get("contact"),
            data.get("created_at"), data.get("confirmed_at"),
            extra_json, gid
        ))
    else:
        cursor.execute(f"""
            INSERT INTO requests
                (tracking_id, grievance_id, service_id, issue, category, department,
                 location, priority, description, language, status, submission_status,
                 submission_mode, government_reference_id, government_status,
                 official_portal, official_helpline, user_name, contact,
                 created_at, confirmed_at, extra_data)
            VALUES ({_placeholders(22)})
        """, (
            tid, gid, data.get("service_id"), data.get("issue"), data.get("category"),
            data.get("department"), data.get("location"), data.get("priority"),
            data.get("description"), data.get("language", "en"),
            data.get("status", "draft"), data.get("submission_status", "draft"),
            data.get("submission_mode", "assisted_handoff"),
            data.get("government_reference_id"), data.get("government_status"),
            data.get("official_portal"), data.get("official_helpline"),
            data.get("user_name"), data.get("contact"),
            data.get("created_at"), data.get("confirmed_at"),
            extra_json
        ))

    conn.commit()
    conn.close()


def get_request(grievance_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    """Retrieve a request by grievance_id or tracking_id."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    ph = _placeholder()
    cursor.execute(
        f"SELECT * FROM requests WHERE grievance_id = {ph} OR tracking_id = {ph}",
        (grievance_id, grievance_id)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = _row_to_dict(row)
    if data.get("extra_data"):
        try:
            extra = json.loads(data["extra_data"])
            data.update(extra)
        except Exception:
            pass
    return data


def update_government_reference(
    grievance_id: str,
    government_reference_id: str,
    government_status: str,
    db_path=None
) -> bool:
    """Link a government reference ID to a Dhvaani request."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    ph = _placeholder()
    cursor.execute(
        f"""UPDATE requests SET government_reference_id={ph}, government_status={ph}
            WHERE grievance_id={ph} OR tracking_id={ph}""",
        (government_reference_id, government_status, grievance_id, grievance_id)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def load_all_requests_to_memory(memory_store: dict, db_path=None):
    """Load existing requests from the database into memory for fast runtime access."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        data = _row_to_dict(row)
        gid = data.get("grievance_id")
        if data.get("extra_data"):
            try:
                extra = json.loads(data["extra_data"])
                data.update(extra)
            except Exception:
                pass
        if gid:
            memory_store[gid] = data


# ──────────────────────────────────────────────
# ATTACHMENT METADATA FUNCTIONS
# ──────────────────────────────────────────────

def save_attachment(meta: Dict[str, Any], db_path=None):
    """Persist attachment metadata to the database."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    ph = _placeholder()
    if _use_postgres:
        cursor.execute("""
            INSERT INTO attachments
                (attachment_id, dhvaani_request_id, original_filename, stored_filename,
                 content_type, file_size, blob_url, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (attachment_id) DO UPDATE SET
                dhvaani_request_id = EXCLUDED.dhvaani_request_id,
                blob_url = EXCLUDED.blob_url
        """, (
            meta["attachment_id"], meta.get("dhvaani_request_id"),
            meta["original_filename"], meta["stored_filename"],
            meta["content_type"], meta["file_size"],
            meta.get("blob_url"), meta["created_at"]
        ))
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO attachments
                (attachment_id, dhvaani_request_id, original_filename, stored_filename,
                 content_type, file_size, blob_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meta["attachment_id"], meta.get("dhvaani_request_id"),
            meta["original_filename"], meta["stored_filename"],
            meta["content_type"], meta["file_size"],
            meta.get("blob_url"), meta["created_at"]
        ))
    conn.commit()
    conn.close()


def get_attachments_for_request(dhvaani_request_id: str, db_path=None) -> List[Dict[str, Any]]:
    """Return all attachment metadata records for a given Dhvaani request."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    ph = _placeholder()
    cursor.execute(
        f"SELECT * FROM attachments WHERE dhvaani_request_id = {ph} ORDER BY created_at",
        (dhvaani_request_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def delete_attachment(attachment_id: str, db_path=None):
    """Delete an attachment metadata record by its attachment_id."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    ph = _placeholder()
    cursor.execute(f"SELECT stored_filename, blob_url FROM attachments WHERE attachment_id = {ph}", (attachment_id,))
    row = cursor.fetchone()
    cursor.execute(f"DELETE FROM attachments WHERE attachment_id = {ph}", (attachment_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success, _row_to_dict(row) if row else None


def link_attachments_to_request(session_attachment_ids: List[str], dhvaani_request_id: str, db_path=None):
    """Link pending session attachments to a confirmed Dhvaani request."""
    if not session_attachment_ids:
        return
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    ph = _placeholder()
    for aid in session_attachment_ids:
        cursor.execute(
            f"UPDATE attachments SET dhvaani_request_id = {ph} WHERE attachment_id = {ph}",
            (dhvaani_request_id, aid)
        )
    conn.commit()
    conn.close()
