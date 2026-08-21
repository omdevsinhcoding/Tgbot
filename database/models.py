"""
Database Models — creates tables and seeds default data.
"""

from database.connection import get_pool


async def create_tables():
    """Create all required tables if they don't exist."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        # ── Settings Table ──────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key         VARCHAR(100) PRIMARY KEY,
                value       TEXT NOT NULL,
                updated_at  TIMESTAMP DEFAULT NOW()
            );
        """)

        # ── Plans Table ─────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id              SERIAL PRIMARY KEY,
                name            VARCHAR(100) NOT NULL,
                description     TEXT DEFAULT '',
                duration_days   INTEGER NOT NULL DEFAULT 30,
                price           DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                max_emails      INTEGER NOT NULL DEFAULT 100,
                is_active       BOOLEAN DEFAULT TRUE,
                created_at      TIMESTAMP DEFAULT NOW()
            );
        """)

        # ── Users Table ─────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              SERIAL PRIMARY KEY,
                telegram_id     BIGINT UNIQUE NOT NULL,
                username        VARCHAR(255) DEFAULT '',
                full_name       VARCHAR(255) DEFAULT '',
                plan_id         INTEGER REFERENCES plans(id) ON DELETE SET NULL,
                plan_expires_at TIMESTAMP,
                is_admin        BOOLEAN DEFAULT FALSE,
                is_banned       BOOLEAN DEFAULT FALSE,
                created_at      TIMESTAMP DEFAULT NOW()
            );
        """)

        # ── Seed default welcome message if not exists ──────────
        existing = await conn.fetchval(
            "SELECT value FROM settings WHERE key = $1",
            "welcome_message"
        )
        if existing is None:
            await conn.execute(
                "INSERT INTO settings (key, value) VALUES ($1, $2)",
                "welcome_message",
                "🎉 *Welcome to IMAP Email Bot!*\n\n"
                "Access your emails directly from Telegram.\n"
                "Choose an option below to get started."
            )


async def init_database():
    """Initialize the database — create tables and seed data."""
    await create_tables()
    print("✅ Database tables created & seeded successfully.")
