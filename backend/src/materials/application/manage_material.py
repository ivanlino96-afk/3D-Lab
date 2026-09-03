from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.audit.domain.entities import AuditEvent
from src.materials.domain.entities import PublicationStatus
from src.materials.domain.publication import MaterialDraft, validate_for_publication


class MaterialAdminRepository(Protocol):
    def get(self, material_id: UUID) -> MaterialDraft | None: ...

    def slug_exists(self, slug: str, excluding_id: UUID | None = None) -> bool: ...

    def save(self, material: MaterialDraft, updated_at: datetime) -> MaterialDraft: ...

    def save_application(
        self, slug: str, name: str, factors: str, display_order: int
    ) -> object: ...

    def save_property_definition(
        self, slug: str, name: str, unit: str, display_order: int
    ) -> object: ...


class AuditRepository(Protocol):
    def append(self, event: AuditEvent) -> None: ...


class MaterialAdminError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ManageMaterial:
    repository: MaterialAdminRepository
    audit: AuditRepository

    def save(
        self, material: MaterialDraft, admin_user_id: UUID, occurred_at: datetime
    ) -> MaterialDraft:
        normalized = replace(
            material,
            slug=material.slug.strip().casefold(),
            name=material.name.strip(),
            description=material.description.strip(),
        )
        if self.repository.slug_exists(normalized.slug, excluding_id=normalized.id):
            raise MaterialAdminError("El identificador del material ya está en uso.")
        if normalized.status is PublicationStatus.PUBLISHED:
            validate_for_publication(normalized, occurred_at.date())
        saved = self.repository.save(normalized, occurred_at)
        self._audit("material_saved", saved, admin_user_id, occurred_at)
        return saved

    def change_status(
        self,
        material_id: UUID,
        status: PublicationStatus,
        admin_user_id: UUID,
        occurred_at: datetime,
    ) -> MaterialDraft:
        material = self.repository.get(material_id)
        if material is None:
            raise MaterialAdminError("El material no existe.")
        changed = replace(material, status=status)
        if status is PublicationStatus.PUBLISHED:
            validate_for_publication(changed, occurred_at.date())
        saved = self.repository.save(changed, occurred_at)
        self._audit(f"material_{status.value}", saved, admin_user_id, occurred_at)
        return saved

    def _audit(
        self, action: str, material: MaterialDraft, admin_user_id: UUID, occurred_at: datetime
    ) -> None:
        self.audit.append(
            AuditEvent(
                actor_type="administrator",
                actor_id=str(admin_user_id),
                action=action,
                entity_type="material",
                entity_id=str(material.id),
                result="success",
                occurred_at=occurred_at,
            )
        )


@dataclass(frozen=True, slots=True)
class ReorderMaterial:
    repository: MaterialAdminRepository
    audit: AuditRepository

    def execute(
        self, material_id: UUID, display_order: int, admin_user_id: UUID, occurred_at: datetime
    ) -> MaterialDraft:
        material = self.repository.get(material_id)
        if material is None:
            raise MaterialAdminError("El material no existe.")
        if display_order < 1:
            raise MaterialAdminError("El orden debe ser mayor que cero.")
        reordered = self.repository.save(
            replace(material, display_order=display_order), occurred_at
        )
        ManageMaterial(self.repository, self.audit)._audit(
            "material_reordered", reordered, admin_user_id, occurred_at
        )
        return reordered


@dataclass(frozen=True, slots=True)
class ManageApplicationDefinition:
    repository: MaterialAdminRepository
    audit: AuditRepository

    def execute(
        self,
        slug: str,
        name: str,
        factors: str,
        display_order: int,
        admin_user_id: UUID,
        occurred_at: datetime,
    ) -> object:
        values = (slug.strip().casefold(), name.strip(), factors.strip())
        if not all(values) or display_order < 1:
            raise MaterialAdminError(
                "Completa identificador, nombre, factores y orden de aplicación."
            )
        saved = self.repository.save_application(*values, display_order)
        self._audit("application_saved", slug, admin_user_id, occurred_at)
        return saved

    def _audit(self, action: str, slug: str, admin_user_id: UUID, occurred_at: datetime) -> None:
        self.audit.append(
            AuditEvent(
                actor_type="administrator",
                actor_id=str(admin_user_id),
                action=action,
                entity_type="material_application",
                entity_id=slug,
                result="success",
                occurred_at=occurred_at,
            )
        )


@dataclass(frozen=True, slots=True)
class ManagePropertyDefinition:
    repository: MaterialAdminRepository
    audit: AuditRepository

    def execute(
        self,
        slug: str,
        name: str,
        unit: str,
        display_order: int,
        admin_user_id: UUID,
        occurred_at: datetime,
    ) -> object:
        values = (slug.strip().casefold(), name.strip(), unit.strip())
        if not all(values) or display_order < 1:
            raise MaterialAdminError("Completa identificador, nombre, unidad y orden de propiedad.")
        saved = self.repository.save_property_definition(*values, display_order)
        self.audit.append(
            AuditEvent(
                actor_type="administrator",
                actor_id=str(admin_user_id),
                action="property_definition_saved",
                entity_type="material_property_definition",
                entity_id=slug,
                result="success",
                occurred_at=occurred_at,
            )
        )
        return saved
