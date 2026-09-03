from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column

from src.materials.domain.entities import (
    Application,
    Certification,
    CostLevel,
    Material,
    MaterialPropertyValue,
    PropertyDefinition,
    PublicationStatus,
)
from src.shared.infrastructure.database import Base

material_applications = Table(
    "material_applications",
    Base.metadata,
    Column("material_id", ForeignKey("materials.id"), primary_key=True),
    Column("application_id", ForeignKey("applications.id"), primary_key=True),
)


class ApplicationRecord(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    factors: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)


class PropertyDefinitionRecord(Base):
    __tablename__ = "property_definitions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)


class MaterialRecord(Base):
    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    advantages: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    cost_level: Mapped[str] = mapped_column(String(10), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_updated_at: Mapped[date] = mapped_column(Date, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False)
    colors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    finishes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MaterialPropertyValueRecord(Base):
    __tablename__ = "material_property_values"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materials.id"), nullable=False)
    property_definition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("property_definitions.id"), nullable=False
    )
    value: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(500))


class CertificationRecord(Base):
    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materials.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    issuer: Mapped[str] = mapped_column(String(140), nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(String(500))
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)


class SqlAlchemyMaterialCatalogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[Material]:
        records = self._session.scalars(
            select(MaterialRecord).order_by(MaterialRecord.display_order, MaterialRecord.name)
        ).all()
        return [self._to_domain(record) for record in records]

    def get_by_slug(self, slug: str) -> Material | None:
        record = self._session.scalar(select(MaterialRecord).where(MaterialRecord.slug == slug))
        return self._to_domain(record) if record else None

    def list_by_slugs(self, slugs: list[str]) -> list[Material]:
        if not slugs:
            return []
        records = self._session.scalars(
            select(MaterialRecord).where(MaterialRecord.slug.in_(slugs))
        ).all()
        by_slug = {record.slug: self._to_domain(record) for record in records}
        return [by_slug[slug] for slug in slugs if slug in by_slug]

    def list_applications(self) -> list[Application]:
        records = self._session.scalars(
            select(ApplicationRecord).order_by(
                ApplicationRecord.display_order, ApplicationRecord.name
            )
        ).all()
        return [self._application_to_domain(record) for record in records]

    def list_property_definitions(self) -> list[PropertyDefinition]:
        records = self._session.scalars(
            select(PropertyDefinitionRecord).order_by(
                PropertyDefinitionRecord.display_order, PropertyDefinitionRecord.name
            )
        ).all()
        return [self._definition_to_domain(record) for record in records]

    def _to_domain(self, record: MaterialRecord) -> Material:
        application_records = self._session.scalars(
            select(ApplicationRecord)
            .join(
                material_applications,
                material_applications.c.application_id == ApplicationRecord.id,
            )
            .where(material_applications.c.material_id == record.id)
            .order_by(ApplicationRecord.display_order)
        ).all()
        property_rows = self._session.execute(
            select(MaterialPropertyValueRecord, PropertyDefinitionRecord)
            .join(
                PropertyDefinitionRecord,
                MaterialPropertyValueRecord.property_definition_id == PropertyDefinitionRecord.id,
            )
            .where(MaterialPropertyValueRecord.material_id == record.id)
            .order_by(PropertyDefinitionRecord.display_order)
        ).all()
        certification_records = self._session.scalars(
            select(CertificationRecord).where(CertificationRecord.material_id == record.id)
        ).all()
        return Material(
            id=record.id,
            slug=record.slug,
            name=record.name,
            description=record.description,
            advantages=tuple(record.advantages),
            limitations=tuple(record.limitations),
            available=record.available,
            cost_level=CostLevel(record.cost_level),
            source_url=record.source_url,
            source_updated_at=record.source_updated_at,
            display_order=record.display_order,
            status=PublicationStatus(record.status),
            applications=tuple(self._application_to_domain(item) for item in application_records),
            properties=tuple(
                MaterialPropertyValue(
                    definition=self._definition_to_domain(definition),
                    value=value.value,
                    source=value.source,
                )
                for value, definition in property_rows
            ),
            certifications=tuple(
                Certification(
                    name=item.name,
                    issuer=item.issuer,
                    evidence_url=item.evidence_url,
                    valid_from=item.valid_from,
                    valid_until=item.valid_until,
                )
                for item in certification_records
            ),
            colors=tuple(record.colors),
            finishes=tuple(record.finishes),
        )

    @staticmethod
    def _application_to_domain(record: ApplicationRecord) -> Application:
        return Application(slug=record.slug, name=record.name, factors=record.factors)

    @staticmethod
    def _definition_to_domain(record: PropertyDefinitionRecord) -> PropertyDefinition:
        return PropertyDefinition(slug=record.slug, name=record.name, unit=record.unit)
