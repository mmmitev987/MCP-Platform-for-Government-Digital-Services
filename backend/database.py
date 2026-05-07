from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings

# Ensure storage directory exists
Path(settings.DB_PATH).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{settings.DB_PATH}",
    connect_args={"check_same_thread": False},
    # Connection pool — supports at least 10 concurrent users
    pool_size=10,        # keep 10 persistent connections open
    max_overflow=20,     # allow 20 extra connections under burst load
    pool_timeout=30,     # wait up to 30s for a free connection before error
    pool_pre_ping=True,  # test connection health before reusing it
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _connection_record):
    """
    Applied once per new SQLite connection.

    WAL mode — allows multiple readers + one writer at the same time.
    Without it, any write locks the entire DB and blocks all other readers.
    This is the single most important change for concurrent users.

    busy_timeout — instead of immediately raising "database is locked",
    SQLite waits up to 5 000 ms for the lock to be released.

    synchronous=NORMAL — safe and faster than the default FULL.
    cache_size / temp_store — keep more data in memory, fewer disk reads.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
