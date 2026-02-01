#!/usr/bin/env python3
"""
Helper script to migrate SHA-256 API keys to bcrypt.
Users must provide their raw keys for reissuing.
"""
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from db.session import SessionLocal
from db.models import ApiKey, User


def show_legacy_keys(db: Session):
    """Show all API keys that need rehashing."""
    print("\n🔍 Legacy API Keys Needing Reissue")
    print("=" * 50)

    legacy_keys = (
        db.query(ApiKey)
        .filter(ApiKey.needs_rehash == True, ApiKey.is_active == True)  # noqa: E712
        .join(User)
        .all()
    )

    if not legacy_keys:
        print("✅ No legacy keys found. Migration complete!")
        return []

    for key in legacy_keys:
        user = key.user
        print(f"\n📋 Key ID: {key.id}")
        print(f"   User: {user.email} (ID: {user.id})")
        print(f"   Label: {key.label}")
        print(f"   Created: {key.created_at}")
        print(f"   Last Used: {key.last_used_at or 'Never'}")

    print(f"\n📊 Total: {len(legacy_keys)} keys need reissuing")
    return legacy_keys


def reissue_single_key(db: Session, key_id: uuid.UUID, new_raw_key: str):
    """Reissue a single API key with bcrypt."""
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        print(f"❌ Key {key_id} not found")
        return False

    key_hash = bcrypt.hashpw(new_raw_key.encode(), bcrypt.gensalt()).decode()

    key.key_hash = key_hash
    key.needs_rehash = False
    key.expires_at = datetime.now(timezone.utc) + timedelta(days=365)

    db.add(key)
    db.commit()

    print(f"✅ Key {key_id} reissued successfully")
    print(f"   New key: {new_raw_key}")
    print("   ⚠️  Save this key - it won't be shown again!")
    return True


def create_migration_key_for_user(db: Session, user_id: uuid.UUID):
    """Create a temporary migration key for a user."""
    import secrets

    raw_key = f"h4k_mig_{secrets.token_urlsafe(24)}"
    key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()

    migration_key = ApiKey(
        id=uuid.uuid4(),
        user_id=user_id,
        key_hash=key_hash,
        label="Migration Temporary Key",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_active=True,
        needs_rehash=False,
    )

    db.add(migration_key)
    db.commit()

    print(f"\n🔑 Created migration key for user {user_id}")
    print(f"   Key: {raw_key}")
    print(f"   Expires: {migration_key.expires_at}")
    print("   Use this to create new permanent keys via API")

    return raw_key


def bulk_disable_legacy_keys(db: Session):
    """Disable all legacy SHA-256 keys after migration period."""
    print("\n🚨 Disabling Legacy SHA-256 Keys")
    print("=" * 50)

    legacy_count = (
        db.query(ApiKey)
        .filter(ApiKey.needs_rehash == True, ApiKey.is_active == True)  # noqa: E712
        .count()
    )

    if legacy_count == 0:
        print("✅ No legacy keys to disable")
        return

    confirmation = input(f"Disable {legacy_count} legacy keys? (yes/no): ")
    if confirmation.lower() != "yes":
        print("❌ Operation cancelled")
        return

    disabled = (
        db.query(ApiKey)
        .filter(ApiKey.needs_rehash == True, ApiKey.is_active == True)  # noqa: E712
        .update({"is_active": False, "revoked_at": datetime.now(timezone.utc)})
    )

    db.commit()

    print(f"✅ Disabled {disabled} legacy keys")
    print("⚠️  Users must now use bcrypt-secured keys")


def main():
    """Main migration helper."""
    print("🔄 HarmonyØ4 API Key Migration Helper")
    print("=" * 50)

    db = SessionLocal()

    try:
        while True:
            print("\nOptions:")
            print("1. Show legacy keys needing reissue")
            print("2. Reissue a specific key (requires raw key)")
            print("3. Create migration key for user")
            print("4. Disable all legacy keys")
            print("5. Exit")

            choice = input("\nSelect option (1-5): ").strip()

            if choice == "1":
                show_legacy_keys(db)
            elif choice == "2":
                key_id = input("Enter key ID to reissue: ").strip()
                try:
                    key_uuid = uuid.UUID(key_id)
                except ValueError:
                    print("❌ Invalid UUID format")
                    continue

                new_key = input("Enter new raw API key: ").strip()
                if not new_key.startswith("h4k_"):
                    print("❌ Key must start with 'h4k_' prefix")
                    continue

                reissue_single_key(db, key_uuid, new_key)
            elif choice == "3":
                user_id = input("Enter user ID: ").strip()
                try:
                    user_uuid = uuid.UUID(user_id)
                except ValueError:
                    print("❌ Invalid UUID format")
                    continue

                create_migration_key_for_user(db, user_uuid)
            elif choice == "4":
                bulk_disable_legacy_keys(db)
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")
    finally:
        db.close()


if __name__ == "__main__":
    main()
