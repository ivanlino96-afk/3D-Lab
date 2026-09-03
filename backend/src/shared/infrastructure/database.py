from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.shared.config import get_settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def build_engine(database_url: str | None = None):
    return create_engine(database_url or get_settings().database_url, pool_pre_ping=True)


engine = build_engine()
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def get_session() -> Iterator[Session]:
    with SessionFactory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session] = SessionFactory) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self.session = self._session_factory()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.session is None:
            return
        if exc_type is not None:
            self.rollback()
        self.session.close()

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("La unidad de trabajo no está activa.")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is not None:
            self.session.rollback()
