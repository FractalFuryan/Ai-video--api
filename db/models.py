import uuid
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    func,
    Index,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped = mapped_column(DateTime(timezone=True), nullable=True)
    needs_rehash: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User")


class MediaFile(Base):
    __tablename__ = "media_files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    h4mk_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    original_name: Mapped[str] = mapped_column(Text, nullable=False)
    uploader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    upload_time: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    public_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    storage_backend: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)

    uploader = relationship("User")
    share_tokens = relationship("ShareToken", back_populates="media", cascade="all, delete-orphan")


Index("ix_media_uploader_time", MediaFile.uploader_id, MediaFile.upload_time)


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    media_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("media_files.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ua: Mapped[str | None] = mapped_column(Text, nullable=True)
    ts: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    media = relationship("MediaFile")


class ShareToken(Base):
    __tablename__ = "share_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    media_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_files.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped = mapped_column(DateTime(timezone=True), nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped = mapped_column(DateTime(timezone=True), nullable=True)

    media = relationship("MediaFile", back_populates="share_tokens")
