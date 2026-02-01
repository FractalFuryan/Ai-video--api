import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from api.deps import db_session, log_access
from api.middleware.auth import get_current_api_key
from db.models import ApiKey
from utils.hashing import hash_api_key_secure

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", status_code=201)
def create_api_key(
    request: Request,
    label: str = "Default",
    expires_days: int = 365,
    current_api_key: ApiKey = Depends(get_current_api_key),
    db: Session = Depends(db_session),
):
    if not current_api_key:
        raise HTTPException(status_code=403, detail="Authentication required")

    if expires_days < 1 or expires_days > 730:
        raise HTTPException(status_code=400, detail="Expiration must be between 1 and 730 days")

    raw_key = f"h4k_{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key_secure(raw_key)
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

    new_key = ApiKey(
        id=uuid.uuid4(),
        user_id=current_api_key.user_id,
        key_hash=key_hash,
        label=label,
        expires_at=expires_at,
        is_active=True,
    )

    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    log_access(db, request, "api_key_create", user_id=current_api_key.user_id, media_id=None)

    return {
        "id": str(new_key.id),
        "api_key": raw_key,
        "label": label,
        "created_at": new_key.created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "warning": "Store this API key securely. It will not be shown again.",
    }


@router.post("/{key_id}/revoke")
def revoke_api_key(
    key_id: str,
    request: Request,
    current_api_key: ApiKey = Depends(get_current_api_key),
    db: Session = Depends(db_session),
):
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid key ID format") from exc

    key_to_revoke = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_uuid, ApiKey.user_id == current_api_key.user_id)
        .first()
    )

    if not key_to_revoke:
        raise HTTPException(status_code=404, detail="API key not found")

    if not key_to_revoke.is_active:
        raise HTTPException(status_code=400, detail="API key already revoked")

    key_to_revoke.is_active = False
    key_to_revoke.revoked_at = datetime.now(timezone.utc)

    db.add(key_to_revoke)
    db.commit()

    log_access(db, request, "api_key_revoke", user_id=current_api_key.user_id, media_id=None)

    return {
        "revoked": True,
        "id": key_id,
        "revoked_at": key_to_revoke.revoked_at.isoformat(),
    }


@router.get("")
def list_api_keys(
    current_api_key: ApiKey = Depends(get_current_api_key),
    db: Session = Depends(db_session),
):
    keys = (
        db.query(ApiKey)
        .filter(ApiKey.user_id == current_api_key.user_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )

    return [
        {
            "id": str(key.id),
            "label": key.label,
            "is_active": key.is_active,
            "created_at": key.created_at.isoformat(),
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
            "needs_rehash": key.needs_rehash,
        }
        for key in keys
    ]
