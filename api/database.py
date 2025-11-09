import asyncpg
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main import JobStatus


class DatabaseError(Exception):
    """Database operation failed"""
    pass


class Database:
    """Database connection pool manager and operations"""

    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self, dsn: str | None) -> None:
        """Initialize database connection pool"""
        if dsn is None:
            raise DatabaseError("DATABASE_URL is not set")
        self.pool = await asyncpg.create_pool(dsn=dsn)

    async def close(self) -> None:
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()

    def _ensure_pool(self) -> asyncpg.Pool:
        """Ensure pool is initialized, raise error if not"""
        if self.pool is None:
            raise DatabaseError("Database pool is not initialized")
        return self.pool

    async def record_error(self, job_id: str, error: str) -> None:
        """
        Record job error in database.

        Raises:
            DatabaseError: If update fails
        """
        pool = self._ensure_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                        UPDATE jobs SET status='error', error=$1, finished_at=$2 WHERE id=$3
                    """,
                    error,
                    datetime.now(timezone.utc),
                    job_id,
                )
        except Exception as e:
            raise DatabaseError(f"Failed to record error for job {job_id}") from e

    async def record_success(self, job_id: str, output_file_id: str) -> None:
        """
        Record job success in database.

        Raises:
            DatabaseError: If update fails
        """
        pool = self._ensure_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                        UPDATE jobs SET status='success', output_file_id=$1, finished_at=$2 WHERE id=$3
                    """,
                    output_file_id,
                    datetime.now(timezone.utc),
                    job_id,
                )
        except Exception as e:
            raise DatabaseError(f"Failed to record success for job {job_id}") from e

    async def create_job(self, file_id: str) -> "JobStatus":
        """
        Create a new job in database.

        Raises:
            DatabaseError: If creation fails
        """
        pool = self._ensure_pool()
        try:
            # Import here to avoid circular dependency
            from .main import JobStatus

            async with pool.acquire() as conn:
                job_row = await conn.fetchrow(
                    """
                        INSERT INTO jobs (input_file_id) VALUES ($1) RETURNING *;
                    """,
                    file_id,
                )

            if job_row is None:
                raise DatabaseError("Failed to create job")

            return JobStatus(**dict(job_row))  # type: ignore
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Failed to create job for file {file_id}") from e

    async def get_job(self, job_id: str) -> "JobStatus | None":
        """
        Get job status from database.

        Returns None if job not found.

        Raises:
            DatabaseError: If query fails
        """
        pool = self._ensure_pool()
        try:
            # Import here to avoid circular dependency
            from .main import JobStatus

            async with pool.acquire() as conn:
                job_row = await conn.fetchrow(
                    """
                        SELECT * FROM jobs WHERE id = $1;
                    """,
                    job_id,
                )

            if job_row is None:
                return None

            return JobStatus(**dict(job_row))  # type: ignore
        except Exception as e:
            raise DatabaseError(f"Failed to get job {job_id}") from e


# Global database instance
db = Database()
