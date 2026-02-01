import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from api.acl import require_owner_access
from api.deps import db_session, log_access
from api.middleware.auth import get_current_api_key
from db.models import ApiKey, MediaFile, ShareToken

router = APIRouter(prefix="/media/{media_id}/share", tags=["share"])


def _generate_share_token() -> tuple[str, str]:
    raw_token = f"h4s_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return raw_token, token_hash


@router.post("", status_code=201)
def create_share_token(
    request: Request,
    media_id: str,
    expires_hours: int = Query(24, ge=1, le=168),
    max_uses: Optional[int] = Query(None, ge=1, le=1000),
    media: MediaFile = Depends(require_owner_access),
    db: Session = Depends(db_session),
    api_key: ApiKey = Depends(get_current_api_key),
):
    raw_token, token_hash = _generate_share_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

    share_token = ShareToken(
        id=uuid.uuid4(),
        media_id=media.id,
        token_hash=token_hash,
        expires_at=expires_at,
        max_uses=max_uses,
        created_at=datetime.now(timezone.utc),
    )

    db.add(share_token)
    db.commit()
    db.refresh(share_token)

    log_access(db, request, "share_token_create", user_id=api_key.user_id, media_id=media.id)

    return {
        "share_token": raw_token,
        "token_id": str(share_token.id),
        "media_id": str(media.id),
        "expires_at": expires_at.isoformat(),
        "max_uses": max_uses,
        "warning": "Share this token carefully. It grants access to this media.",
    }


@router.get("")
def list_share_tokens(
    media_id: str,
    media: MediaFile = Depends(require_owner_access),
    db: Session = Depends(db_session),
    api_key: ApiKey = Depends(get_current_api_key),
):
    now = datetime.now(timezone.utc)
    tokens = (
        db.query(ShareToken)
        .filter(ShareToken.media_id == media.id)
        .order_by(ShareToken.created_at.desc())
        .all()
    )

    log_access(db, None, "share_token_list", user_id=api_key.user_id, media_id=media.id)

    return [
        {
            "id": str(token.id),
            "created_at": token.created_at.isoformat(),
            "expires_at": token.expires_at.isoformat(),
            "max_uses": token.max_uses,
            "usage_count": token.usage_count,
            "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
            "is_active": token.expires_at > now
            and (token.max_uses is None or token.usage_count < token.max_uses),
        }
        for token in tokens
    ]


@router.delete("/{token_id}")
def revoke_share_token(
    media_id: str,
    token_id: str,
    media: MediaFile = Depends(require_owner_access),
    db: Session = Depends(db_session),
    api_key: ApiKey = Depends(get_current_api_key),
):
    try:
        token_uuid = uuid.UUID(token_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid token ID") from exc

    token = (
        db.query(ShareToken)
        .filter(ShareToken.id == token_uuid, ShareToken.media_id == media.id)
        .first()
    )

    if not token:
        raise HTTPException(status_code=404, detail="Share token not found")

    token.expires_at = datetime.now(timezone.utc)
    db.add(token)
    db.commit()

    log_access(db, None, "share_token_revoke", user_id=api_key.user_id, media_id=media.id)

    return {"revoked": True, "token_id": token_id}


@router.delete("")
def revoke_all_share_tokens(
    media_id: str,
    media: MediaFile = Depends(require_owner_access),
    db: Session = Depends(db_session),
    api_key: ApiKey = Depends(get_current_api_key),
):
    now = datetime.now(timezone.utc)
    db.query(ShareToken).filter(ShareToken.media_id == media.id).update({"expires_at": now})
    db.commit()

    log_access(db, None, "share_token_revoke_all", user_id=api_key.user_id, media_id=media.id)

    return {"revoked": True, "media_id": media_id}
