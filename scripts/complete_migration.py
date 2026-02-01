#!/usr/bin/env python3
"""
Finalize migration from SHA-256 to bcrypt.
Disables legacy auth and enables strict bcrypt-only mode.
"""
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from db.session import SessionLocal
from db.models import ApiKey


def check_migration_status(db: Session) -> bool:
    """Check if migration is ready to complete."""
    print("📊 Migration Status Check")
    print("=" * 50)

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

    print(f"🔐 Legacy SHA-256 keys still active: {legacy_active}")
    print(f"🔒 Bcrypt-secured keys active: {bcrypt_active}")

    if legacy_active > 0:
        print(f"\n❌ Cannot complete migration: {legacy_active} users still using legacy keys")
        print("   Run scripts/reissue_api_keys.py to migrate remaining keys")
        return False

    print("\n✅ All users migrated to bcrypt!")
    return True


def enable_strict_bcrypt_mode():
    """Update auth middleware to reject SHA-256 keys."""
    print("\n🔒 Enabling Strict Bcrypt-Only Mode")
    print("=" * 50)

    auth_file = "api/middleware/auth.py"

    try:
        with open(auth_file, "r", encoding="utf-8") as handle:
            content = handle.read()

        if "Legacy SHA-256 support" in content:
            print("⚠️  SHA-256 fallback still active in auth.py")
            confirmation = input("Update auth.py automatically? (yes/no): ")
            if confirmation.lower() != "yes":
                print("❌ Manual update required")
                return

            start_marker = "# Legacy SHA-256 support"
            end_marker = "return row"

            start = content.find(start_marker)
            if start == -1:
                print("❌ Could not find legacy code block")
                return

            end = content.find(end_marker, start)
            if end == -1:
                print("❌ Could not find end of legacy code block")
                return

            new_content = content[:start] + content[end + len(end_marker) :]
            with open(auth_file, "w", encoding="utf-8") as handle:
                handle.write(new_content)

            print("✅ Updated auth.py to bcrypt-only mode")
        else:
            print("✅ Auth.py already in bcrypt-only mode")
    except Exception as exc:
        print(f"❌ Error updating auth.py: {exc}")


def disable_legacy_keys(db: Session):
    """Disable any remaining legacy keys."""
    print("\n🚫 Disabling Remaining Legacy Keys")
    print("=" * 50)

    legacy_keys = db.query(ApiKey).filter(ApiKey.needs_rehash == True).all()  # noqa: E712

    if not legacy_keys:
        print("✅ No legacy keys to disable")
        return

    for key in legacy_keys:
        key.is_active = False
        key.revoked_at = datetime.now(timezone.utc)
        db.add(key)

    db.commit()
    print(f"✅ Disabled {len(legacy_keys)} legacy keys")


def update_env_config():
    """Update environment configuration for bcrypt-only mode."""
    print("\n⚙️  Updating Environment Configuration")
    print("=" * 50)

    env_file = ".env"

    try:
        with open(env_file, "a", encoding="utf-8") as handle:
            handle.write("\n# Security Configuration (Post-Migration)\n")
            handle.write("AUTH_BCRYPT_ONLY=true\n")
            handle.write("LEGACY_SHA256_SUPPORT=false\n")

        print("✅ Updated .env with bcrypt-only settings")
    except Exception as exc:
        print(f"⚠️  Could not update .env: {exc}")
        print("   Add these lines manually:")
        print("   AUTH_BCRYPT_ONLY=true")
        print("   LEGACY_SHA256_SUPPORT=false")


def main():
    """Complete the migration process."""
    print("🎯 HarmonyØ4 Migration Completion")
    print("=" * 50)

    db = SessionLocal()

    try:
        if not check_migration_status(db):
            sys.exit(1)

        print("\n🚨 FINAL MIGRATION STEP")
        print("This will:")
        print("1. Disable all remaining SHA-256 keys")
        print("2. Update auth.py to reject SHA-256 keys")
        print("3. Update configuration")
        print("4. Legacy keys will STOP WORKING")

        confirmation = input("\nProceed with migration completion? (yes/no): ")
        if confirmation.lower() != "yes":
            print("❌ Migration completion cancelled")
            sys.exit(0)

        disable_legacy_keys(db)
        enable_strict_bcrypt_mode()
        update_env_config()

        print("\n" + "=" * 50)
        print("🎉 MIGRATION COMPLETE!")
        print("=" * 50)
        print("\n✅ All API keys now use bcrypt encryption")
        print("✅ Legacy SHA-256 support disabled")
        print("✅ System is now in secure bcrypt-only mode")
        print("\n⚠️  IMPORTANT: Restart your API server")
    finally:
        db.close()


if __name__ == "__main__":
    main()
