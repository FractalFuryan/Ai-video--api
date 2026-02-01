import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import db_session
from api.middleware.auth import get_current_api_key, optional_api_key
from db.models import ApiKey, MediaFile, ShareToken


class ACL:
    @staticmethod
    def check_media_access(
        db: Session,
        media_id: str,
        api_key: Optional[ApiKey] = None,
        share_token: Optional[str] = None,
        require_owner: bool = False,
    ) -> MediaFile:
        try:
            media_uuid = uuid.UUID(media_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid media ID format") from exc

        media = db.query(MediaFile).filter(MediaFile.id == media_uuid).first()
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")

        # Owner always has access
        if api_key and str(media.uploader_id) == str(api_key.user_id):
            return media

        # Owner required for this operation
        if require_owner:
            raise HTTPException(status_code=403, detail="Owner access required")

        # Public access
        if media.public_access:
            return media

        # Share token access
        if share_token and ACL.verify_share_token(db, str(media.id), share_token):
            return media

        raise HTTPException(status_code=403, detail="Access denied")

    @staticmethod
    def verify_share_token(db: Session, media_id: str, raw_token: str) -> bool:
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)

        share = (
            db.query(ShareToken)
            .filter(
                ShareToken.media_id == uuid.UUID(media_id),
                ShareToken.token_hash == token_hash,
                ShareToken.expires_at > now,
            )
            .first()
        )

        if not share:
            return False

        if share.max_uses is not None and share.usage_count >= share.max_uses:
            return False

        share.usage_count += 1
        share.last_used_at = now
        db.add(share)
        db.commit()
        return True


def require_media_access(
    media_id: str,
    share_token: Optional[str] = Query(None),
    api_key: Optional[ApiKey] = Depends(optional_api_key),
    db: Session = Depends(db_session),
) -> MediaFile:
    return ACL.check_media_access(
        db=db,
        media_id=media_id,
        api_key=api_key,
        share_token=share_token,
        require_owner=False,
    )


def require_owner_access(
    media_id: str,
    api_key: ApiKey = Depends(get_current_api_key),
    db: Session = Depends(db_session),
) -> MediaFile:
    return ACL.check_media_access(
        db=db,
        media_id=media_id,
        api_key=api_key,
        require_owner=True,
    )
