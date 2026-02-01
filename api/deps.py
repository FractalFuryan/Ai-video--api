from fastapi import Request
from sqlalchemy.orm import Session

from db.models import AccessLog
from db.session import SessionLocal
from storage.factory import get_storage


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def storage_backend():
    return get_storage()


def log_access(db: Session, request: Request | None, action: str, user_id=None, media_id=None):
    ip = request.client.host if request and request.client else None
    ua = request.headers.get("user-agent") if request else None
    path = str(request.url.path) if request else ""
    row = AccessLog(
        user_id=user_id,
        media_id=media_id,
        action=action,
        path=path,
        ip=ip,
        ua=ua,
    )
    db.add(row)
    db.commit()
