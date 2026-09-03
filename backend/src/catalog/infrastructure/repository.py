from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Integer, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from src.catalog.domain.entities import Service
from src.shared.infrastructure.database import Base


class ServiceRecord(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class SqlAlchemyServiceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_published(self) -> list[Service]:
        statement = (
            select(ServiceRecord)
            .where(ServiceRecord.is_published.is_(True))
            .order_by(ServiceRecord.display_order, ServiceRecord.name)
        )
        records = self._session.scalars(statement).all()
        return [
            Service(
                id=record.id,
                slug=record.slug,
                name=record.name,
                summary=record.summary,
                description=record.description,
                display_order=record.display_order,
                is_published=record.is_published,
            )
            for record in records
        ]
