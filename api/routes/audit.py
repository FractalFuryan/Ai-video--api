from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from api.deps import db_session, log_access
from api.middleware.auth import get_current_api_key
from db.models import AccessLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/recent")
def recent_access_logs(
    request: Request,
    limit: int = 50,
    api_key=Depends(get_current_api_key),
    db: Session = Depends(db_session),
):
    limit = max(1, min(limit, 250))
    rows = (
        db.query(AccessLog)
        .order_by(AccessLog.ts.desc())
        .limit(limit)
        .all()
    )

    log_access(
        db,
        request,
        "audit_recent",
        user_id=api_key.user_id if api_key else None,
        media_id=None,
    )

    return [
        {
            "id": str(row.id),
            "user_id": str(row.user_id) if row.user_id else None,
            "media_id": str(row.media_id) if row.media_id else None,
            "action": row.action,
            "path": row.path,
            "ip": row.ip,
            "ua": row.ua,
            "ts": row.ts.isoformat(),
        }
        for row in rows
    ]
