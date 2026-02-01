from datetime import datetime, timezone
from fastapi import Security, HTTPException, Request
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from config import settings
from db.models import ApiKey
from db.session import SessionLocal
from utils.hashing import sha256_hex_text, verify_api_key_secure

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def _db() -> Session:
    return SessionLocal()


def _find_valid_key(db: Session, raw_key: str) -> ApiKey | None:
    now = datetime.now(timezone.utc)
    rows = (
        db.query(ApiKey)
        .filter(ApiKey.is_active == True)  # noqa: E712
        .all()
    )

    for row in rows:
        if row.expires_at and row.expires_at <= now:
            continue
        if row.revoked_at is not None:
            continue
        if verify_api_key_secure(raw_key, row.key_hash):
            row.last_used_at = now
            db.add(row)
            db.commit()
            return row

        # Legacy SHA-256 support (temporary migration window)
        if row.key_hash == sha256_hex_text(raw_key):
            row.last_used_at = now
            row.needs_rehash = True
            db.add(row)
            db.commit()
            return row

    return None


async def get_current_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> ApiKey | None:
    """
    Returns ApiKey row if valid, else raises. If API_KEYS_ENABLED=false, returns None.
    """
    if not settings.API_KEYS_ENABLED:
        return None

    if not api_key or len(api_key) < 16:
        raise HTTPException(status_code=403, detail="Missing or invalid API key")

    db = _db()
    try:
        row = _find_valid_key(db, api_key)
        if not row:
            raise HTTPException(status_code=403, detail="Invalid API key")
        return row
    finally:
        db.close()


async def optional_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> ApiKey | None:
    if not settings.API_KEYS_ENABLED:
        return None
    if not api_key:
        return None

    db = _db()
    try:
        return _find_valid_key(db, api_key)
    finally:
        db.close()


# Backwards-compatible alias
require_api_key = get_current_api_key
