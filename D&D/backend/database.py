"""SQLAlchemy persistence and transaction boundaries; independent from bridge DB."""
import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    default = Path(__file__).resolve().parents[1] / "data" / "arcanum.sqlite3"
    return os.environ.get("ARCANUM_DATABASE_URL", f"sqlite:///{default.as_posix()}")


def build_engine(url: str):
    options = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False, "timeout": 30}
        if url in ("sqlite://", "sqlite:///:memory:"):
            options["poolclass"] = StaticPool
        else:
            from sqlalchemy.engine import make_url
            db = make_url(url).database
            if db:
                Path(db).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, **options)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def configure_sqlite(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=30000")
            connection.execute("PRAGMA journal_mode=WAL")
    return engine


def session_factory(engine):
    return sessionmaker(engine, class_=Session, expire_on_commit=False)

