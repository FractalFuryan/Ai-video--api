"""Admin endpoints for system management and monitoring."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.deps import db_session
from api.middleware.auth import get_current_api_key
from db.models import ApiKey, MediaFile, ShareToken, User
from utils.hashing import hash_api_key_secure

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(
    api_key=Depends(get_current_api_key),
    db: Session = Depends(db_session),
) -> User:
    user = (
        db.query(User)
        .filter(
            User.id == api_key.user_id,
            User.is_active == True,  # noqa: E712
            User.is_admin == True,  # noqa: E712
        )
        .first()
    )

    if not user:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


@router.get("/migration-status")
def get_migration_status(
    admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> dict[str, Any]:
    legacy_active = (
        db.query(ApiKey)
        .filter(ApiKey.needs_rehash == True, ApiKey.is_active == True)  # noqa: E712
        .count()
    )
    bcrypt_active = (
        db.query(ApiKey)
        .filter(ApiKey.needs_rehash == False, ApiKey.is_active == True)  # noqa: E712
        .count()
    )

    users_with_legacy = (
        db.query(func.count(func.distinct(ApiKey.user_id)))
        .filter(ApiKey.needs_rehash == True, ApiKey.is_active == True)  # noqa: E712
        .scalar()
        or 0
    )
    total_users = db.query(func.count(User.id)).scalar() or 0

    since_7_days = datetime.now(timezone.utc) - timedelta(days=7)
    recent_legacy_usage = (
        db.query(ApiKey)
        .filter(
            ApiKey.needs_rehash == True,  # noqa: E712
            ApiKey.is_active == True,  # noqa: E712
            ApiKey.last_used_at.isnot(None),
            ApiKey.last_used_at >= since_7_days,
        )
        .count()
    )

    now = datetime.now(timezone.utc)
    expiring_soon = (
        db.query(ApiKey)
        .filter(
            ApiKey.is_active == True,  # noqa: E712
            ApiKey.expires_at.isnot(None),
            ApiKey.expires_at <= now + timedelta(days=30),
            ApiKey.expires_at > now,
        )
        .count()
    )
    expired = (
        db.query(ApiKey)
        .filter(
            ApiKey.is_active == True,  # noqa: E712
            ApiKey.expires_at.isnot(None),
            ApiKey.expires_at <= now,
        )
        .count()
    )

    total_keys = bcrypt_active + legacy_active
    progress = 100.0 if total_keys == 0 else round(bcrypt_active / total_keys * 100, 1)

    return {
        "security": {
            "legacy_keys_active": legacy_active,
            "bcrypt_keys_active": bcrypt_active,
            "migration_progress_percent": progress,
            "users_with_legacy_keys": users_with_legacy,
            "recent_legacy_usage": recent_legacy_usage,
            "key_expiration": {
                "expiring_soon_30d": expiring_soon,
                "expired": expired,
            },
        },
        "users": {
            "total_users": total_users,
            "active_users": db.query(User).filter(User.is_active == True).count(),  # noqa: E712
            "admin_users": db.query(User)
            .filter(User.is_admin == True, User.is_active == True)  # noqa: E712
            .count(),
        },
        "media": {
            "total_media": db.query(MediaFile).count(),
            "public_media": db.query(MediaFile)
            .filter(MediaFile.public_access == True)  # noqa: E712
            .count(),
            "total_size_bytes": db.query(func.coalesce(func.sum(MediaFile.file_size), 0)).scalar()
            or 0,
        },
        "system": {
            "active_share_tokens": db.query(ShareToken)
            .filter(ShareToken.expires_at > now)
            .count(),
            "timestamp": now.isoformat(),
        },
    }


@router.get("/users/{user_id}/api-keys")
def get_user_api_keys(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> list[dict[str, Any]]:
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user ID") from exc

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    keys = (
        db.query(ApiKey)
        .filter(ApiKey.user_id == user_uuid)
        .order_by(ApiKey.created_at.desc())
        .all()
    )

    return [
        {
            "id": str(key.id),
            "label": key.label,
            "is_active": key.is_active,
            "needs_rehash": key.needs_rehash,
            "created_at": key.created_at.isoformat(),
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
        }
        for key in keys
    ]


@router.post("/users/{user_id}/force-migrate")
def force_user_migration(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> dict[str, Any]:
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user ID") from exc

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    legacy_keys = (
        db.query(ApiKey)
        .filter(
            ApiKey.user_id == user_uuid,
            ApiKey.needs_rehash == True,  # noqa: E712
            ApiKey.is_active == True,  # noqa: E712
        )
        .all()
    )

    disabled_count = 0
    for key in legacy_keys:
        key.is_active = False
        key.revoked_at = datetime.now(timezone.utc)
        db.add(key)
        disabled_count += 1

    raw_key = f"h4k_mig_{uuid.uuid4().hex}"
    key_hash = hash_api_key_secure(raw_key)

    migration_key = ApiKey(
        id=uuid.uuid4(),
        user_id=user_uuid,
        key_hash=key_hash,
        label="Admin Migration Key",
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
        is_active=True,
        needs_rehash=False,
    )

    db.add(migration_key)
    db.commit()

    return {
        "user_id": user_id,
        "user_email": user.email,
        "legacy_keys_disabled": disabled_count,
        "migration_key": raw_key,
        "migration_key_id": str(migration_key.id),
        "expires_at": migration_key.expires_at.isoformat(),
        "note": "Provide this temporary key to the user. It expires in 3 days.",
    }


@router.get("/audit/logs")
def get_audit_logs(
    days: int = Query(7, ge=1, le=90),
    action: str | None = Query(None),
    admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> dict[str, Any]:
    return {
        "message": "Audit log endpoint placeholder. Implement when audit log model is ready.",
        "parameters": {"days": days, "action": action},
        "note": "Create an AuditLog model and query it here.",
    }
