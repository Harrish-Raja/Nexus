"""Entry point 1: create the database, its tables and the seeded sign-in accounts."""

import os
import secrets

from config import config


def main():
    """Create what is missing and leave what exists exactly as it is."""
    os.makedirs(config.DATABASE_DIRECTORY, exist_ok=True)

    from access.password_security import hash_password
    from persistence.database import SessionFactory, database_engine
    from persistence.models import Base, UserAccount
    from persistence.repository import fetch_user_account, insert_user_account

    Base.metadata.create_all(database_engine)
    print(f"database: {config.APPLICATION_DATABASE_FILE}")
    print(f"  tables: {', '.join(sorted(Base.metadata.tables))}")

    created, present = 0, 0
    with SessionFactory() as session:
        for account in config.SEED_USER_ACCOUNTS:
            if fetch_user_account(session, UserAccount.username == account["username"]):
                present += 1
                continue
            salt = secrets.token_hex(config.PASSWORD_SALT_BYTES)
            insert_user_account(session, {
                "username": account["username"],
                "display_name": account["display_name"],
                "role": account["role"],
                "password_salt": salt,
                "password_hash": hash_password(account["password"], salt),
            })
            created += 1
            print(f"  account created  {account['username']:<12}{account['display_name']:<22}"
                  f"{account['role']}")
    print(f"  accounts created: {created}, already present: {present}")
    return created


if __name__ == "__main__":
    main()
