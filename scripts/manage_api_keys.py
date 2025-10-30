#!/usr/bin/env python3
"""
API Key Management Script

Utilities for creating, listing, and managing API keys for the Trading CLI API.
"""

import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path


# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def create_api_key(name: str, scopes: list[str], rate_limit: int = 60):
    """Create a new API key."""
    from app.api.core.database import db_manager
    from app.api.core.security import generate_api_key, hash_api_key
    from app.api.models.auth import APIKeyModel

    # Generate key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    # Save to database
    db_manager.create_async_engine()
    async with db_manager.get_async_session() as session:
        db_key = APIKeyModel(
            id=uuid.uuid4(),
            key_hash=key_hash,
            name=name,
            scopes=scopes,
            rate_limit=rate_limit,
            is_active=True,
            created_at=datetime.utcnow(),
        )

        session.add(db_key)
        await session.commit()

    print("✅ API Key created successfully!")
    print(f"Name: {name}")
    print(f"Scopes: {', '.join(scopes)}")
    print(f"Rate Limit: {rate_limit} req/min")
    print("\n⚠️  IMPORTANT: Save this key securely - it won't be shown again!")
    print(f"\nAPI Key: {api_key}")
    print("\nUse in requests:")
    print(f"X-API-Key: {api_key}")

    await db_manager.dispose()


async def list_api_keys():
    """List all API keys."""
    from sqlalchemy import select

    from app.api.core.database import db_manager
    from app.api.models.auth import APIKeyModel

    db_manager.create_async_engine()
    async with db_manager.get_async_session() as session:
        result = await session.execute(select(APIKeyModel))
        keys = result.scalars().all()

        if not keys:
            print("No API keys found.")
            return

        print(f"\n📋 API Keys ({len(keys)} total)\n")
        print(
            f"{'Name':<30} {'Scopes':<30} {'Rate Limit':<15} {'Status':<10} {'Created'}"
        )
        print("=" * 110)

        for key in keys:
            scopes_str = ", ".join(key.scopes[:3])
            if len(key.scopes) > 3:
                scopes_str += "..."
            status = "Active" if key.is_active else "Inactive"
            created = key.created_at.strftime("%Y-%m-%d %H:%M")

            print(
                f"{key.name:<30} {scopes_str:<30} {key.rate_limit:<15} {status:<10} {created}"
            )

    await db_manager.dispose()


async def deactivate_api_key(key_id: str):
    """Deactivate an API key."""
    from sqlalchemy import select

    from app.api.core.database import db_manager
    from app.api.models.auth import APIKeyModel

    db_manager.create_async_engine()
    async with db_manager.get_async_session() as session:
        result = await session.execute(
            select(APIKeyModel).where(APIKeyModel.id == uuid.UUID(key_id))
        )
        key = result.scalar_one_or_none()

        if not key:
            print(f"❌ API key not found: {key_id}")
            return

        key.is_active = False
        await session.commit()

        print(f"✅ API key deactivated: {key.name}")

    await db_manager.dispose()


def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage Trading CLI API keys")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new API key")
    create_parser.add_argument("name", help="Name for the API key")
    create_parser.add_argument(
        "--scopes",
        nargs="+",
        default=["*"],
        help="Scopes (command groups or '*' for all)",
    )
    create_parser.add_argument(
        "--rate-limit", type=int, default=60, help="Rate limit (requests per minute)"
    )

    # List command
    subparsers.add_parser("list", help="List all API keys")

    # Deactivate command
    deactivate_parser = subparsers.add_parser(
        "deactivate", help="Deactivate an API key"
    )
    deactivate_parser.add_argument("key_id", help="API key ID to deactivate")

    args = parser.parse_args()

    if args.command == "create":
        asyncio.run(create_api_key(args.name, args.scopes, args.rate_limit))
    elif args.command == "list":
        asyncio.run(list_api_keys())
    elif args.command == "deactivate":
        asyncio.run(deactivate_api_key(args.key_id))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
