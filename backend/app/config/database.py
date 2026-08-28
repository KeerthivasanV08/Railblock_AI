"""
Database configuration stub for RailBlock AI.

STATUS: NOT CONNECTED / FUTURE INTEGRATION

The current project uses a CSV-first data architecture. No database is
connected. This module is an architecture placeholder for a future
PostgreSQL (or equivalent) integration.

When database integration is added:
- Add DATABASE_URL to Settings (config/settings.py)
- Add SQLAlchemy engine/session setup here
- Add Alembic migrations under backend/migrations/alembic/
- Update repositories/ to use ORM models instead of CSV reads
"""

# Future: from sqlalchemy import create_engine
# Future: from sqlalchemy.orm import sessionmaker
# Future: from app.config.settings import settings

DATABASE_AVAILABLE = False
DATABASE_STATUS = "NOT_CONNECTED"
DATABASE_TYPE = "FUTURE_POSTGRESQL"

# Placeholder — no actual connection is made
DATABASE_URL: str = ""  # Will be read from settings.DATABASE_URL when implemented
