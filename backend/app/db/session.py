from collections.abc import Generator, Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def get_database_url() -> str:
    return get_settings().database_url


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def repeatable_read_only_session(bind: Engine) -> Iterator[Session]:
    """Own one non-mutating snapshot and always end it with rollback."""
    connection = bind.connect()
    if bind.dialect.name == "postgresql":
        connection = connection.execution_options(
            isolation_level="REPEATABLE READ",
        )
    transaction = connection.begin()
    db = Session(bind=connection, autoflush=False, expire_on_commit=False)
    try:
        if bind.dialect.name == "postgresql":
            db.execute(text("SET TRANSACTION READ ONLY"))
        yield db
    finally:
        db.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
