#!/usr/bin/env python3
"""Telegram authentication helper for OpenClaw benchmark client."""

import sys
from pathlib import Path

from config import load_config
from telegram_client import TelegramClient


def authenticate() -> bool:
    """Authenticate with Telegram and save session.

    Returns:
        True if authentication succeeded, False otherwise
    """
    print("=" * 60)
    print("OpenClaw Telegram Authentication")
    print("=" * 60)
    print()

    config = load_config()

    # Check if session already exists
    session_file = Path(f"{config.telegram_session_name}.session")
    if session_file.exists():
        print(f"ℹ️  Session file already exists: {session_file}")
        print("   Attempting to use existing session...")
        print()

    print(f"📱 Phone number: {config.telegram_phone}")
    print(f"🤖 Bot username: @{config.openclaw_bot_username}")
    print()
    print("Note: You will receive a verification code via Telegram app.")
    print("      Check your Telegram and enter the code when prompted.")
    print()

    try:
        with TelegramClient(config) as client:
            me = client.get_me_sync()
            print()
            print("✅ Authentication successful!")
            print(f"   Logged in as: {me['first_name']}")
            if me.get('username'):
                print(f"   Username: @{me['username']}")
            print(f"   Phone: {me['phone_number']}")
            print()
            print(f"💾 Session saved to: {session_file}")
            print()
            print("You can now run benchmarks without re-authenticating:")
            print("  just bench file --telegram")
            print("  just bench-all --telegram")
            print()
            return True

    except KeyboardInterrupt:
        print()
        print("❌ Authentication cancelled by user.")
        return False
    except Exception as e:
        print()
        print(f"❌ Authentication failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check your .env file has correct credentials")
        print("  2. Verify your phone number format (+country_code + number)")
        print("  3. Make sure you entered the correct verification code")
        print("  4. Try running 'just auth' again")
        return False


def main() -> int:
    """Main entry point."""
    success = authenticate()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
