"""Lazy shared SQLAlchemy engine. Driver connection is deferred until first use."""
from sqlalchemy import create_engine
from config.config import DB_URL

_engine = None

def get_engine():
    """Return the shared engine, creating it on first use."""
    global _engine
    if _engine is None:
        _engine = create_engine(DB_URL, future=True, pool_pre_ping=True)
    return _engine
