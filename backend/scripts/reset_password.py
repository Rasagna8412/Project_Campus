"""Project Campus — Safe Administrative Password Reset Utility.

Provides a secure, audited CLI for administrators to reset a student or user password
during controlled pilots without exposing public endpoints or accepting passwords
as command-line arguments.

Usage:
    python scripts/reset_password.py --email student@example.com
    docker compose exec backend python scripts/reset_password.py --email student@example.com
"""

import argparse
import asyncio
import getpass
from pathlib import Path
import sys
from typing import Optional, Tuple

# Ensure backend directory is in sys.path when executed directly
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash, verify_password
from app.models.identity import User, UserRole


async def get_user_by_email(email: str, session: AsyncSession) -> Optional[User]:
    """Retrieve user entity with loaded roles for administrative inspection."""
    normalized_email = email.strip().lower()
    query = (
        select(User)
        .where(User.email == normalized_email)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def reset_user_password(
    email: str,
    new_password: str,
    session: Optional[AsyncSession] = None,
) -> Tuple[bool, str]:
    """Safely update a user's password using standard bcrypt hashing.

    Guarantees:
    - Never accepts passwords as command-line arguments.
    - Never logs passwords or hashes.
    - Enforces minimum 8-character password length.
    - Uses application's existing bcrypt configuration (12 rounds).
    - Wraps update in a database transaction with rollback on failure.

    Returns:
        Tuple[bool, str]: (success, status_message)
    """
    normalized_email = email.strip().lower()
    if not normalized_email:
        return False, "Target email address cannot be empty."

    if not new_password or len(new_password) < 8:
        return False, "Password must be at least 8 characters long."

    close_session_at_end = False
    if session is None:
        session = AsyncSessionLocal()
        close_session_at_end = True

    try:
        user = await get_user_by_email(normalized_email, session)
        if not user:
            return False, f"User with email '{normalized_email}' not found."

        # Compute authoritative bcrypt hash with 12 rounds
        new_hash = get_password_hash(new_password)
        user.hashed_password = new_hash

        await session.commit()
        return True, f"Password successfully reset for user '{normalized_email}'."
    except Exception as exc:
        await session.rollback()
        return False, f"Database transaction failed: {exc}"
    finally:
        if close_session_at_end:
            await session.close()


def main() -> None:
    """Execute interactive administrative password reset."""
    parser = argparse.ArgumentParser(
        description="Administrative CLI to securely reset a student or user password."
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address of the target account to reset.",
    )
    parser.add_argument(
        "--assume-yes",
        action="store_true",
        help="Skip interactive confirmation (for non-interactive execution).",
    )

    args = parser.parse_args()
    email = args.email.strip().lower()

    async def _inspect_and_prompt() -> None:
        async with AsyncSessionLocal() as session:
            user = await get_user_by_email(email, session)
            if not user:
                print(
                    f"Error: No user account found with email: '{email}'",
                    file=sys.stderr,
                )
                sys.exit(1)

            role_names = [ur.role.name for ur in user.user_roles if ur.role]

            print("=" * 65)
            print("PROJECT CAMPUS — ADMINISTRATIVE PASSWORD RESET")
            print("=" * 65)
            print(f"Target User ID : {user.id}")
            print(f"Full Name      : {user.full_name}")
            print(f"Email          : {user.email}")
            print(f"Roles          : {', '.join(role_names) if role_names else 'None'}")
            print(f"Active Status  : {'Active' if user.is_active else 'Deactivated'}")
            print("=" * 65)

            if not args.assume_yes:
                confirm = (
                    input(
                        f"Are you sure you want to reset the password for '{email}'? (yes/no): "
                    )
                    .strip()
                    .lower()
                )
                if confirm != "yes":
                    print("Operation cancelled by administrator.", file=sys.stderr)
                    sys.exit(0)

            # Secure password prompts without echoing to terminal
            try:
                pwd1 = getpass.getpass("Enter new password (min 8 chars): ")
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.", file=sys.stderr)
                sys.exit(1)

            if not pwd1 or len(pwd1) < 8:
                print(
                    "Error: Password must be at least 8 characters long.",
                    file=sys.stderr,
                )
                sys.exit(1)

            try:
                pwd2 = getpass.getpass("Confirm new password: ")
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.", file=sys.stderr)
                sys.exit(1)

            if pwd1 != pwd2:
                print("Error: Passwords do not match.", file=sys.stderr)
                sys.exit(1)

            success, message = await reset_user_password(email, pwd1, session=session)
            if success:
                print(f"SUCCESS: {message}")
                sys.exit(0)
            else:
                print(f"FAILURE: {message}", file=sys.stderr)
                sys.exit(1)

    asyncio.run(_inspect_and_prompt())


if __name__ == "__main__":
    main()
