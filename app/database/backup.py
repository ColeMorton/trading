"""
Database Backup and Restore Utilities

This module provides utilities for backing up and restoring the PostgreSQL database
and Redis cache, with support for scheduled backups and point-in-time recovery.
"""

import asyncio
import gzip
import json
import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from app.database.config import get_database_settings

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database backups and restores."""

    def __init__(self):
        self.settings = get_database_settings()
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    async def create_full_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a full backup of PostgreSQL and Redis."""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        logger.info(f"Creating full backup: {backup_name}")

        try:
            # Backup PostgreSQL
            postgres_backup = await self._backup_postgresql(backup_path)

            # Backup Redis
            redis_backup = await self._backup_redis(backup_path)

            # Create backup metadata
            metadata = {
                "backup_name": backup_name,
                "timestamp": datetime.now().isoformat(),
                "type": "full",
                "postgresql_backup": postgres_backup,
                "redis_backup": redis_backup,
                "database_url": str(self.settings.database_url),
                "redis_url": str(self.settings.redis_url),
            }

            metadata_file = backup_path / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            # Compress the backup
            compressed_backup = await self._compress_backup(backup_path)

            logger.info(f"Full backup completed: {compressed_backup}")
            return str(compressed_backup)

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            # Cleanup failed backup
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise

    async def _backup_postgresql(self, backup_path: Path) -> str:
        """Backup PostgreSQL database using pg_dump."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_file = backup_path / f"postgresql_{timestamp}.sql"

        # Prepare pg_dump command
        cmd = [
            "pg_dump",
            "--host",
            self.settings.database_host,
            "--port",
            str(self.settings.database_port),
            "--username",
            self.settings.database_user,
            "--dbname",
            self.settings.database_name,
            "--no-password",
            "--verbose",
            "--clean",
            "--if-exists",
            "--create",
            "--file",
            str(dump_file),
        ]

        # Set environment variables for authentication
        env = os.environ.copy()
        env["PGPASSWORD"] = self.settings.database_password

        logger.info(f"Running pg_dump to {dump_file}")

        try:
            result = subprocess.run(
                cmd, env=env, capture_output=True, text=True, check=True
            )

            logger.info("PostgreSQL backup completed successfully")
            return str(dump_file)

        except subprocess.CalledProcessError as e:
            logger.error(f"pg_dump failed: {e.stderr}")
            raise RuntimeError(f"PostgreSQL backup failed: {e.stderr}")

    async def _backup_redis(self, backup_path: Path) -> str:
        """Backup Redis data."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        redis_file = backup_path / f"redis_{timestamp}.json"

        try:
            # Connect to Redis
            redis_client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                password=self.settings.redis_password,
                db=self.settings.redis_db,
                decode_responses=True,
            )

            # Get all keys
            keys = await redis_client.keys("*")

            # Export all data
            redis_data = {}
            for key in keys:
                key_type = await redis_client.type(key)

                if key_type == "string":
                    redis_data[key] = {
                        "type": "string",
                        "value": await redis_client.get(key),
                        "ttl": await redis_client.ttl(key),
                    }
                elif key_type == "hash":
                    redis_data[key] = {
                        "type": "hash",
                        "value": await redis_client.hgetall(key),
                        "ttl": await redis_client.ttl(key),
                    }
                elif key_type == "list":
                    redis_data[key] = {
                        "type": "list",
                        "value": await redis_client.lrange(key, 0, -1),
                        "ttl": await redis_client.ttl(key),
                    }
                elif key_type == "set":
                    redis_data[key] = {
                        "type": "set",
                        "value": list(await redis_client.smembers(key)),
                        "ttl": await redis_client.ttl(key),
                    }
                elif key_type == "zset":
                    redis_data[key] = {
                        "type": "zset",
                        "value": await redis_client.zrange(key, 0, -1, withscores=True),
                        "ttl": await redis_client.ttl(key),
                    }

            # Save to file
            with open(redis_file, "w") as f:
                json.dump(redis_data, f, indent=2)

            await redis_client.close()

            logger.info(f"Redis backup completed: {len(keys)} keys exported")
            return str(redis_file)

        except Exception as e:
            logger.error(f"Redis backup failed: {e}")
            raise RuntimeError(f"Redis backup failed: {e}")

    async def _compress_backup(self, backup_path: Path) -> Path:
        """Compress backup directory."""
        compressed_file = backup_path.with_suffix(".tar.gz")

        try:
            # Create compressed archive
            cmd = [
                "tar",
                "-czf",
                str(compressed_file),
                "-C",
                str(backup_path.parent),
                backup_path.name,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Remove uncompressed directory
            shutil.rmtree(backup_path)

            logger.info(f"Backup compressed: {compressed_file}")
            return compressed_file

        except subprocess.CalledProcessError as e:
            logger.error(f"Backup compression failed: {e.stderr}")
            raise RuntimeError(f"Backup compression failed: {e.stderr}")

    async def restore_backup(self, backup_file: str, force: bool = False) -> bool:
        """Restore from a backup file."""
        backup_path = Path(backup_file)

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        logger.info(f"Restoring from backup: {backup_file}")

        try:
            # Extract compressed backup
            if backup_path.suffix == ".gz":
                extracted_path = await self._extract_backup(backup_path)
            else:
                extracted_path = backup_path

            # Load metadata
            metadata_file = extracted_path / "metadata.json"
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            logger.info(f"Restoring backup from {metadata['timestamp']}")

            # Restore PostgreSQL
            if metadata.get("postgresql_backup"):
                postgres_file = (
                    extracted_path / Path(metadata["postgresql_backup"]).name
                )
                await self._restore_postgresql(postgres_file, force)

            # Restore Redis
            if metadata.get("redis_backup"):
                redis_file = extracted_path / Path(metadata["redis_backup"]).name
                await self._restore_redis(redis_file, force)

            # Cleanup extracted files if they were compressed
            if backup_path.suffix == ".gz" and extracted_path != backup_path:
                shutil.rmtree(extracted_path)

            logger.info("Backup restore completed successfully")
            return True

        except Exception as e:
            logger.error(f"Backup restore failed: {e}")
            raise

    async def _extract_backup(self, backup_file: Path) -> Path:
        """Extract compressed backup."""
        extract_dir = backup_file.parent / backup_file.stem.replace(".tar", "")

        try:
            cmd = ["tar", "-xzf", str(backup_file), "-C", str(backup_file.parent)]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return extract_dir

        except subprocess.CalledProcessError as e:
            logger.error(f"Backup extraction failed: {e.stderr}")
            raise RuntimeError(f"Backup extraction failed: {e.stderr}")

    async def _restore_postgresql(self, dump_file: Path, force: bool = False):
        """Restore PostgreSQL database from dump file."""
        if not force:
            logger.warning(
                "PostgreSQL restore requires force=True to prevent accidental data loss"
            )
            raise RuntimeError("PostgreSQL restore requires force=True")

        cmd = [
            "psql",
            "--host",
            self.settings.database_host,
            "--port",
            str(self.settings.database_port),
            "--username",
            self.settings.database_user,
            "--dbname",
            "postgres",  # Connect to postgres db first
            "--no-password",
            "--file",
            str(dump_file),
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = self.settings.database_password

        logger.info(f"Restoring PostgreSQL from {dump_file}")

        try:
            result = subprocess.run(
                cmd, env=env, capture_output=True, text=True, check=True
            )

            logger.info("PostgreSQL restore completed successfully")

        except subprocess.CalledProcessError as e:
            logger.error(f"PostgreSQL restore failed: {e.stderr}")
            raise RuntimeError(f"PostgreSQL restore failed: {e.stderr}")

    async def _restore_redis(self, redis_file: Path, force: bool = False):
        """Restore Redis data from backup file."""
        if not force:
            logger.warning(
                "Redis restore requires force=True to prevent accidental data loss"
            )
            raise RuntimeError("Redis restore requires force=True")

        try:
            # Connect to Redis
            redis_client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                password=self.settings.redis_password,
                db=self.settings.redis_db,
                decode_responses=True,
            )

            # Clear existing data
            await redis_client.flushdb()

            # Load backup data
            with open(redis_file, "r") as f:
                redis_data = json.load(f)

            # Restore data
            for key, data in redis_data.items():
                key_type = data["type"]
                value = data["value"]
                ttl = data.get("ttl", -1)

                if key_type == "string":
                    await redis_client.set(key, value)
                elif key_type == "hash":
                    await redis_client.hset(key, mapping=value)
                elif key_type == "list":
                    await redis_client.lpush(key, *reversed(value))
                elif key_type == "set":
                    await redis_client.sadd(key, *value)
                elif key_type == "zset":
                    # Convert list of [member, score] pairs to dict
                    zset_data = {member: score for member, score in value}
                    await redis_client.zadd(key, zset_data)

                # Set TTL if it was set in the original
                if ttl > 0:
                    await redis_client.expire(key, ttl)

            await redis_client.close()

            logger.info(f"Redis restore completed: {len(redis_data)} keys restored")

        except Exception as e:
            logger.error(f"Redis restore failed: {e}")
            raise RuntimeError(f"Redis restore failed: {e}")

    async def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []

        for backup_file in self.backup_dir.glob("backup_*.tar.gz"):
            try:
                # Extract just the metadata
                cmd = [
                    "tar",
                    "-xzf",
                    str(backup_file),
                    "-C",
                    "/tmp",
                    f"{backup_file.stem}/metadata.json",
                ]
                subprocess.run(cmd, capture_output=True, check=True)

                metadata_file = Path("/tmp") / backup_file.stem / "metadata.json"
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

                backups.append(
                    {
                        "file": str(backup_file),
                        "name": metadata.get("backup_name"),
                        "timestamp": metadata.get("timestamp"),
                        "type": metadata.get("type"),
                        "size": backup_file.stat().st_size,
                    }
                )

                # Cleanup
                shutil.rmtree(Path("/tmp") / backup_file.stem)

            except Exception as e:
                logger.warning(f"Could not read metadata for {backup_file}: {e}")

        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)

    async def cleanup_old_backups(self, keep_days: int = 30):
        """Remove backups older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        backups = await self.list_backups()
        removed_count = 0

        for backup in backups:
            backup_date = datetime.fromisoformat(backup["timestamp"])
            if backup_date < cutoff_date:
                try:
                    os.remove(backup["file"])
                    logger.info(f"Removed old backup: {backup['name']}")
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Failed to remove backup {backup['file']}: {e}")

        logger.info(f"Cleanup completed: removed {removed_count} old backups")
        return removed_count


async def create_backup(backup_name: Optional[str] = None) -> str:
    """Convenience function to create a backup."""
    manager = BackupManager()
    return await manager.create_full_backup(backup_name)


async def restore_backup(backup_file: str, force: bool = False) -> bool:
    """Convenience function to restore from backup."""
    manager = BackupManager()
    return await manager.restore_backup(backup_file, force)


async def list_backups() -> List[Dict[str, Any]]:
    """Convenience function to list backups."""
    manager = BackupManager()
    return await manager.list_backups()


if __name__ == "__main__":
    import sys

    async def main():
        logging.basicConfig(level=logging.INFO)

        if len(sys.argv) < 2:
            print("Usage: python backup.py <command> [args]")
            print("Commands:")
            print("  create [name]     - Create a new backup")
            print("  restore <file>    - Restore from backup (requires --force)")
            print("  list              - List available backups")
            print(
                "  cleanup [days]    - Remove backups older than X days (default: 30)"
            )
            return

        command = sys.argv[1]
        manager = BackupManager()

        try:
            if command == "create":
                backup_name = sys.argv[2] if len(sys.argv) > 2 else None
                result = await manager.create_full_backup(backup_name)
                print(f"Backup created: {result}")

            elif command == "restore":
                if len(sys.argv) < 3:
                    print("Error: backup file required")
                    return

                backup_file = sys.argv[2]
                force = "--force" in sys.argv

                if not force:
                    print(
                        "Warning: This will overwrite existing data. Use --force to confirm."
                    )
                    return

                await manager.restore_backup(backup_file, force=True)
                print("Backup restored successfully")

            elif command == "list":
                backups = await manager.list_backups()
                print(f"Found {len(backups)} backups:")
                for backup in backups:
                    size_mb = backup["size"] / (1024 * 1024)
                    print(
                        f"  {backup['name']} - {backup['timestamp']} ({size_mb:.1f}MB)"
                    )

            elif command == "cleanup":
                days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
                removed = await manager.cleanup_old_backups(days)
                print(f"Removed {removed} old backups")

            else:
                print(f"Unknown command: {command}")

        except Exception as e:
            print(f"Error: {e}")
            return 1

    asyncio.run(main())
