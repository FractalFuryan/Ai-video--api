#!/usr/bin/env python3
"""
Bootstrap initial admin user and API key.
Run this once during initial setup.
"""
import uuid
import bcrypt
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from db.session import SessionLocal, engine
from db.models import Base, User, ApiKey


def setup_database():
    """Ensure database tables exist."""
    print("🗄️  Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ready")


def create_admin_user(db: Session, email: str = "admin@harmony4.local") -> User:
    """Create or get admin user."""
    print(f"👤 Setting up admin user: {email}")

    admin = db.query(User).filter(User.email == email).first()

    if admin:
        print(f"⚠️  Admin user already exists (ID: {admin.id})")
        return admin

    admin = User(
        id=uuid.uuid4(),
        email=email,
        is_active=True,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    print(f"✅ Created admin user: {email} (ID: {admin.id})")
    return admin


def create_admin_api_key(db: Session, user: User, label: str = "Initial Admin Key") -> str:
    """Create initial admin API key."""
    print("🔑 Creating admin API key...")

    raw_key = f"h4k_{secrets.token_urlsafe(32)}"
    key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()

    api_key = ApiKey(
        id=uuid.uuid4(),
        user_id=user.id,
        key_hash=key_hash,
        label=label,
        expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_active=True,
        needs_rehash=False,
    )

    db.add(api_key)
    db.commit()

    print("✅ Created admin API key")
    return raw_key


def create_default_config():
    """Create default system configuration (placeholder)."""
    print("⚙️  Creating default configuration...")
    print("✅ Configuration ready")


def main():
    """Main bootstrap function."""
    print("🚀 HarmonyØ4 Admin Bootstrap")
    print("=" * 50)

    email = input("Admin email [admin@harmony4.local]: ").strip()
    if not email:
        email = "admin@harmony4.local"

    db = SessionLocal()

    try:
        setup_database()
        admin_user = create_admin_user(db, email)
        admin_key = create_admin_api_key(db, admin_user)
        create_default_config()

        print("\n" + "=" * 50)
        print("🎉 Bootstrap Complete!")
        print("=" * 50)
        print(f"\n📧 Admin User: {admin_user.email}")
        print(f"🆔 User ID: {admin_user.id}")
        print(f"🔑 API Key: {admin_key}")
        print("\n⚠️  CRITICAL: Save this API key securely!")
        print("   It will not be shown again.")
        print("\n📝 Next steps:")
        print("1. Use this API key to authenticate requests")
        print("2. Configure storage backend in .env")
        print("3. Start the server: uvicorn api.main:app --reload")
    except Exception as exc:
        print(f"❌ Bootstrap failed: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
