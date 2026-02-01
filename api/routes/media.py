import uuid
from fastapi import APIRouter, UploadFile, File, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from api.acl import require_media_access, require_owner_access
from api.deps import db_session, storage_backend, log_access
from api.middleware.auth import get_current_api_key, optional_api_key, require_api_key
from config import settings
from db.models import MediaFile
from storage.base import StorageBackend
from utils.hashing import sha256_hex

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload")
async def upload_h4mk(
    request: Request,
    file: UploadFile = File(...),
    api_key=Depends(require_api_key),
    db: Session = Depends(db_session),
    storage: StorageBackend = Depends(storage_backend),
):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty upload")

    h = sha256_hex(raw)
    existing = db.query(MediaFile).filter(MediaFile.h4mk_hash == h).first()
    if existing:
        log_access(
            db,
            request,
            "upload",
            user_id=api_key.user_id if api_key else None,
            media_id=existing.id,
        )
        return {"id": str(existing.id), "h4mk_hash": h, "deduped": True}

    key = f"{h[:2]}/{h}.h4mk"
    storage.put(key, raw)

    row = MediaFile(
        h4mk_hash=h,
        original_name=file.filename or "upload.h4mk",
        uploader_id=api_key.user_id if api_key else uuid.uuid4(),
        metadata={"domain": "h4mk", "sealed": True},
        public_access=False,
        storage_backend=settings.STORAGE_BACKEND,
        storage_key=key,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    log_access(db, request, "upload", user_id=row.uploader_id, media_id=row.id)
    return {"id": str(row.id), "h4mk_hash": h, "deduped": False}


@router.get("/{media_id}")
def get_media_meta(
    request: Request,
    media_id: str,
    media: MediaFile = Depends(require_media_access),
    api_key=Depends(optional_api_key),
    db: Session = Depends(db_session),
):
    log_access(
        db,
        request,
        "meta",
        user_id=api_key.user_id if api_key else None,
        media_id=media.id,
    )
    return {
        "id": str(media.id),
        "h4mk_hash": media.h4mk_hash,
        "original_name": media.original_name,
        "upload_time": media.upload_time.isoformat(),
        "metadata": media.metadata,
        "public_access": media.public_access,
        "is_owner": bool(api_key and str(media.uploader_id) == str(api_key.user_id)),
    }


@router.patch("/{media_id}/visibility")
def update_media_visibility(
    request: Request,
    media_id: str,
    public_access: bool,
    media: MediaFile = Depends(require_owner_access),
    api_key=Depends(get_current_api_key),
    db: Session = Depends(db_session),
):
    media.public_access = public_access
    db.add(media)
    db.commit()

    log_access(
        db,
        request,
        "media_visibility_update",
        user_id=api_key.user_id,
        media_id=media.id,
    )

    return {"updated": True, "public_access": public_access}
