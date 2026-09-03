from datetime import UTC, date, datetime
from uuid import UUID

import pytest

from src.materials.application.manage_material import (
    ManageApplicationDefinition,
    ManageMaterial,
    ManagePropertyDefinition,
    MaterialAdminError,
    ReorderMaterial,
)
from src.materials.domain.entities import Certification, CostLevel, PublicationStatus
from src.materials.domain.publication import (
    MaterialDraft,
    MaterialPublicationError,
    validate_for_publication,
)

NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)


def draft(**changes) -> MaterialDraft:
    values = {
        "id": UUID(int=1),
        "slug": "nylon-cf",
        "name": "Nylon CF",
        "description": "Material reforzado para piezas mecánicas exigentes.",
        "advantages": ("Alta rigidez",),
        "limitations": ("Requiere secado",),
        "available": True,
        "cost_level": CostLevel.HIGH,
        "source_url": "https://example.com/nylon-cf",
        "source_updated_at": date(2026, 8, 1),
        "display_order": 2,
        "status": PublicationStatus.DRAFT,
        "application_slugs": ("mechanical",),
        "property_values": (),
        "certifications": (),
        "colors": ("Negro",),
        "finishes": ("Mate",),
    }
    values.update(changes)
    return MaterialDraft(**values)


class FakeRepository:
    def __init__(self) -> None:
        self.items = {}
        self.historical_references = {UUID(int=1): 3}

    def get(self, material_id):
        return self.items.get(material_id)

    def slug_exists(self, slug, excluding_id=None):
        return any(item.slug == slug and item.id != excluding_id for item in self.items.values())

    def save(self, material, updated_at):
        self.items[material.id] = material
        self.updated_at = updated_at
        return material

    def save_application(self, slug, name, factors, display_order):
        return (slug, name, factors, display_order)

    def save_property_definition(self, slug, name, unit, display_order):
        return (slug, name, unit, display_order)


class FakeAudit:
    def __init__(self) -> None:
        self.events = []

    def append(self, event) -> None:
        self.events.append(event)


@pytest.mark.unit
def test_create_edit_and_reorder_material_generate_audit() -> None:
    repository = FakeRepository()
    audit = FakeAudit()
    use_case = ManageMaterial(repository, audit)

    created = use_case.save(draft(), UUID(int=9), NOW)
    edited = use_case.save(draft(name="Nylon CF Pro"), UUID(int=9), NOW)
    ordered = ReorderMaterial(repository, audit).execute(created.id, 1, UUID(int=9), NOW)

    assert edited.name == "Nylon CF Pro"
    assert ordered.display_order == 1
    assert len(audit.events) == 3


@pytest.mark.unit
def test_publishing_reports_every_missing_required_field() -> None:
    incomplete = draft(
        name="",
        description="",
        advantages=(),
        limitations=(),
        source_url="",
        application_slugs=(),
        status=PublicationStatus.PUBLISHED,
    )

    with pytest.raises(MaterialPublicationError) as error:
        validate_for_publication(incomplete, NOW.date())

    assert set(error.value.fields) >= {
        "name",
        "description",
        "advantages",
        "limitations",
        "source_url",
        "applications",
    }


@pytest.mark.unit
def test_expired_or_unsupported_certification_cannot_be_published() -> None:
    expired = Certification(
        "Uso regulado",
        "Laboratorio",
        "https://example.com/evidence",
        date(2024, 1, 1),
        date(2025, 1, 1),
    )
    no_evidence = Certification(
        "Contacto alimentario", "Laboratorio", None, date(2026, 1, 1), date(2027, 1, 1)
    )

    with pytest.raises(MaterialPublicationError) as error:
        validate_for_publication(
            draft(
                status=PublicationStatus.PUBLISHED,
                certifications=(expired, no_evidence),
            ),
            NOW.date(),
        )

    assert "certifications" in error.value.fields


@pytest.mark.unit
def test_publish_and_archive_keep_the_same_material_identity() -> None:
    repository = FakeRepository()
    audit = FakeAudit()
    manager = ManageMaterial(repository, audit)
    manager.save(draft(), UUID(int=9), NOW)

    published = manager.change_status(UUID(int=1), PublicationStatus.PUBLISHED, UUID(int=9), NOW)
    archived = manager.change_status(UUID(int=1), PublicationStatus.ARCHIVED, UUID(int=9), NOW)

    assert published.status is PublicationStatus.PUBLISHED
    assert archived.id == UUID(int=1)
    assert archived.status is PublicationStatus.ARCHIVED
    assert repository.historical_references[archived.id] == 3


@pytest.mark.unit
def test_duplicate_slug_is_rejected_without_overwriting_existing_material() -> None:
    repository = FakeRepository()
    repository.save(draft(id=UUID(int=2), slug="pla"), NOW)

    with pytest.raises(MaterialAdminError, match="identificador"):
        ManageMaterial(repository, FakeAudit()).save(draft(slug="pla"), UUID(int=9), NOW)


@pytest.mark.unit
def test_application_and_property_definitions_require_complete_values() -> None:
    repository = FakeRepository()
    audit = FakeAudit()
    application = ManageApplicationDefinition(repository, audit).execute(
        "medical", "Médico", "Biocompatibilidad", 3, UUID(int=9), NOW
    )
    property_definition = ManagePropertyDefinition(repository, audit).execute(
        "hardness", "Dureza", "Shore D", 4, UUID(int=9), NOW
    )

    assert application[0] == "medical"
    assert property_definition[2] == "Shore D"
    with pytest.raises(MaterialAdminError, match="Completa"):
        ManagePropertyDefinition(repository, audit).execute(
            "", "Sin identificador", "MPa", 1, UUID(int=9), NOW
        )
