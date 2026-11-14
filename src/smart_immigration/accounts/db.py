"""Connexion à la base de données.

PostgreSQL en vrai (variable DATABASE_URL), SQLite par défaut pour développer et tester.
Exemple : DATABASE_URL=postgresql+psycopg://smartimm:change-me-locally@localhost:5432/smartimm
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_SQLITE = Path(__file__).resolve().parents[3] / "data" / "private" / "app.sqlite3"


class Base(DeclarativeBase):
    pass


def make_engine(url: str | None = None) -> Engine:
    url = url or os.environ.get("DATABASE_URL")
    if not url:
        DEFAULT_SQLITE.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{DEFAULT_SQLITE}"
    kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {"pool_pre_ping": True}
    if url.endswith(":memory:"):
        from sqlalchemy.pool import StaticPool
        kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


_engine: Engine | None = None
_factory: sessionmaker[Session] | None = None


def configure(url: str | None = None) -> Engine:
    """(Re)configure la base et crée les tables. Appelé au démarrage et par les tests."""
    global _engine, _factory
    from . import models  # noqa: F401  (enregistre les tables)
    _engine = make_engine(url)
    _factory = sessionmaker(_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)
    return _engine


def get_session() -> Iterator[Session]:
    if _factory is None:
        configure()
    assert _factory is not None
    with _factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
