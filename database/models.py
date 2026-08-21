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

        # ── IMAP Accounts Table ────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS imap_accounts (
                id          SERIAL PRIMARY KEY,
                email       VARCHAR(255) UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                host        VARCHAR(255) NOT NULL DEFAULT 'imap.gmail.com',
                port        INTEGER NOT NULL DEFAULT 993,
                label       VARCHAR(100) DEFAULT '',
                is_active   BOOLEAN DEFAULT TRUE,
                created_at  TIMESTAMP DEFAULT NOW()
            );
        """)

        # ── User-IMAP Assignment Table (many-to-many) ─────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_imap_assignments (
                id              SERIAL PRIMARY KEY,
                telegram_id     BIGINT NOT NULL,
                imap_account_id INTEGER NOT NULL REFERENCES imap_accounts(id) ON DELETE CASCADE,
                assigned_at     TIMESTAMP DEFAULT NOW(),
                assigned_by     BIGINT DEFAULT 0,
                UNIQUE(telegram_id, imap_account_id)
            );
        """)

        # ── Mail Rules Table ──────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id          SERIAL PRIMARY KEY,
                rule_type   VARCHAR(50) NOT NULL,
                rule_value  TEXT NOT NULL
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
                "🎉 Welcome to IMAP Email Bot!\n\n"
                "Access your emails directly from Telegram.\n"
                "Choose an option below to get started."
            )

        # ── Seed default mail rules ────────────────────────────
        rule_count = await conn.fetchval("SELECT COUNT(*) FROM rules")
        if rule_count == 0:
            # Sender allow rules
            for val in ["info@account.netflix.com", "@netflix.com"]:
                await conn.execute(
                    "INSERT INTO rules (rule_type, rule_value) VALUES ($1, $2)",
                    "sender_allow", val,
                )
            # Household subject rules
            for val in ["update your netflix household", "how to update your netflix household",
                        "Important: How to update your Netflix household"]:
                await conn.execute(
                    "INSERT INTO rules (rule_type, rule_value) VALUES ($1, $2)",
                    "household_subject", val,
                )
            # Temp subject rules
            for val in ["temporary access code", "your netflix temporary access code",
                        "Your Netflix temporary access code"]:
                await conn.execute(
                    "INSERT INTO rules (rule_type, rule_value) VALUES ($1, $2)",
                    "temp_subject", val,
                )
            # Link patterns
            for val in ["travel/verify", "update-primary-location", "nftoken=", "messageGuid="]:
                await conn.execute(
                    "INSERT INTO rules (rule_type, rule_value) VALUES ($1, $2)",
                    "link_pattern", val,
                )


async def init_database():
    """Initialize the database — create tables and seed data."""
    await create_tables()
    print("✅ Database tables created & seeded successfully.")
