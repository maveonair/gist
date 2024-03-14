import logging

from sqlalchemy import StaticPool, create_engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from .configuration import Configuration

configuration = Configuration()

engine = create_engine(
    configuration.db_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@event.listens_for(engine, "connect")
def set_sqlite_pragma(
    dbapi_connection: DBAPIConnection, connection_record: ConnectionPoolEntry
):
    try:
        with dbapi_connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout = 5000")
            cursor.execute("PRAGMA synchronous = NORMAL")
    except Exception as e:
        logging.error(f"Error setting PRAGMA: {e}")