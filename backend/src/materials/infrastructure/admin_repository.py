from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from src.materials.domain.entities import Certification, CostLevel, PublicationStatus
from src.materials.domain.publication import AdminPropertyValue, MaterialDraft
from src.materials.infrastructure.repository import (
    ApplicationRecord,
    CertificationRecord,
    MaterialPropertyValueRecord,
    MaterialRecord,
    PropertyDefinitionRecord,
    material_applications,
)


class SqlAlchemyMaterialAdminRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> tuple[MaterialDraft, ...]:
        records = self._session.scalars(
            select(MaterialRecord).order_by(MaterialRecord.display_order, MaterialRecord.name)
        ).all()
        return tuple(self._to_draft(record) for record in records)

    def get(self, material_id: uuid.UUID) -> MaterialDraft | None:
        record = self._session.get(MaterialRecord, material_id)
        return self._to_draft(record) if record else None

    def slug_exists(self, slug: str, excluding_id: uuid.UUID | None = None) -> bool:
        query = select(MaterialRecord.id).where(MaterialRecord.slug == slug)
        if excluding_id:
            query = query.where(MaterialRecord.id != excluding_id)
        return self._session.scalar(query) is not None

    def save(self, material: MaterialDraft, updated_at: datetime) -> MaterialDraft:
        record = self._session.get(MaterialRecord, material.id)
        if record is None:
            record = MaterialRecord(id=material.id)
            self._session.add(record)
        record.slug = material.slug
        record.name = material.name
        record.description = material.description
        record.advantages = list(material.advantages)
        record.limitations = list(material.limitations)
        record.available = material.available
        record.cost_level = material.cost_level.value
        record.source_url = material.source_url
        record.source_updated_at = material.source_updated_at
        record.display_order = material.display_order
        record.status = material.status.value
        record.colors = list(material.colors)
        record.finishes = list(material.finishes)
        record.updated_at = updated_at
        self._session.flush()
        self._replace_relations(material)
        self._session.flush()
        return self._to_draft(record)

    def list_applications(self) -> tuple[ApplicationRecord, ...]:
        return tuple(
            self._session.scalars(
                select(ApplicationRecord).order_by(
                    ApplicationRecord.display_order, ApplicationRecord.name
                )
            ).all()
        )

    def list_property_definitions(self) -> tuple[PropertyDefinitionRecord, ...]:
        return tuple(
            self._session.scalars(
                select(PropertyDefinitionRecord).order_by(
                    PropertyDefinitionRecord.display_order, PropertyDefinitionRecord.name
                )
            ).all()
        )

    def save_application(
        self, slug: str, name: str, factors: str, display_order: int
    ) -> ApplicationRecord:
        record = self._session.scalar(
            select(ApplicationRecord).where(ApplicationRecord.slug == slug)
        )
        if record is None:
            record = ApplicationRecord(id=uuid.uuid4(), slug=slug)
            self._session.add(record)
        record.name = name
        record.factors = factors
        record.display_order = display_order
        self._session.flush()
        return record

    def save_property_definition(
        self, slug: str, name: str, unit: str, display_order: int
    ) -> PropertyDefinitionRecord:
        record = self._session.scalar(
            select(PropertyDefinitionRecord).where(PropertyDefinitionRecord.slug == slug)
        )
        if record is None:
            record = PropertyDefinitionRecord(id=uuid.uuid4(), slug=slug)
            self._session.add(record)
        record.name = name
        record.unit = unit
        record.display_order = display_order
        self._session.flush()
        return record

    def _replace_relations(self, material: MaterialDraft) -> None:
        self._session.execute(
            delete(material_applications).where(material_applications.c.material_id == material.id)
        )
        if material.application_slugs:
            applications = self._session.scalars(
                select(ApplicationRecord).where(
                    ApplicationRecord.slug.in_(material.application_slugs)
                )
            ).all()
            if len(applications) != len(set(material.application_slugs)):
                raise LookupError("Una aplicación seleccionada ya no existe.")
            self._session.execute(
                insert(material_applications),
                [{"material_id": material.id, "application_id": item.id} for item in applications],
            )

        self._session.execute(
            delete(MaterialPropertyValueRecord).where(
                MaterialPropertyValueRecord.material_id == material.id
            )
        )
        if material.property_values:
            definitions = self._session.scalars(
                select(PropertyDefinitionRecord).where(
                    PropertyDefinitionRecord.slug.in_(
                        [item.definition_slug for item in material.property_values]
                    )
                )
            ).all()
            by_slug = {item.slug: item for item in definitions}
            if len(by_slug) != len({item.definition_slug for item in material.property_values}):
                raise LookupError("Una propiedad seleccionada ya no existe.")
            self._session.add_all(
                [
                    MaterialPropertyValueRecord(
                        id=uuid.uuid4(),
                        material_id=material.id,
                        property_definition_id=by_slug[item.definition_slug].id,
                        value=item.value,
                        source=item.source,
                    )
                    for item in material.property_values
                ]
            )

        self._session.execute(
            delete(CertificationRecord).where(CertificationRecord.material_id == material.id)
        )
        self._session.add_all(
            [
                CertificationRecord(
                    id=uuid.uuid4(),
                    material_id=material.id,
                    name=item.name,
                    issuer=item.issuer,
                    evidence_url=item.evidence_url,
                    valid_from=item.valid_from,
                    valid_until=item.valid_until,
                )
                for item in material.certifications
            ]
        )

    def _to_draft(self, record: MaterialRecord) -> MaterialDraft:
        application_slugs = tuple(
            self._session.scalars(
                select(ApplicationRecord.slug)
                .join(
                    material_applications,
                    material_applications.c.application_id == ApplicationRecord.id,
                )
                .where(material_applications.c.material_id == record.id)
                .order_by(ApplicationRecord.display_order)
            ).all()
        )
        property_rows = self._session.execute(
            select(MaterialPropertyValueRecord, PropertyDefinitionRecord.slug)
            .join(
                PropertyDefinitionRecord,
                MaterialPropertyValueRecord.property_definition_id == PropertyDefinitionRecord.id,
            )
            .where(MaterialPropertyValueRecord.material_id == record.id)
        ).all()
        certifications = self._session.scalars(
            select(CertificationRecord).where(CertificationRecord.material_id == record.id)
        ).all()
        return MaterialDraft(
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
            application_slugs=application_slugs,
            property_values=tuple(
                AdminPropertyValue(slug, value.value, value.source) for value, slug in property_rows
            ),
            certifications=tuple(
                Certification(
                    item.name,
                    item.issuer,
                    item.evidence_url,
                    item.valid_from,
                    item.valid_until,
                )
                for item in certifications
            ),
            colors=tuple(record.colors),
            finishes=tuple(record.finishes),
        )
