from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from src.materials.domain.entities import Certification, CostLevel, PublicationStatus

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True, slots=True)
class AdminPropertyValue:
    definition_slug: str
    value: float | None
    source: str | None


@dataclass(frozen=True, slots=True)
class MaterialDraft:
    id: UUID
    slug: str
    name: str
    description: str
    advantages: tuple[str, ...]
    limitations: tuple[str, ...]
    available: bool
    cost_level: CostLevel
    source_url: str
    source_updated_at: date
    display_order: int
    status: PublicationStatus
    application_slugs: tuple[str, ...] = field(default_factory=tuple)
    property_values: tuple[AdminPropertyValue, ...] = field(default_factory=tuple)
    certifications: tuple[Certification, ...] = field(default_factory=tuple)
    colors: tuple[str, ...] = field(default_factory=tuple)
    finishes: tuple[str, ...] = field(default_factory=tuple)


class MaterialPublicationError(ValueError):
    def __init__(self, fields: list[str]) -> None:
        self.fields = tuple(fields)
        super().__init__("Faltan o son inválidos estos campos: " + ", ".join(fields) + ".")


def validate_for_publication(material: MaterialDraft, on_date: date) -> None:
    missing = []
    required_text = {
        "name": material.name,
        "description": material.description,
        "source_url": material.source_url,
    }
    missing.extend(name for name, value in required_text.items() if not value.strip())
    if not SLUG_PATTERN.fullmatch(material.slug):
        missing.append("slug")
    if not material.advantages:
        missing.append("advantages")
    if not material.limitations:
        missing.append("limitations")
    if not material.application_slugs:
        missing.append("applications")
    if material.display_order < 1:
        missing.append("display_order")
    if any(not certification.is_public(on_date) for certification in material.certifications):
        missing.append("certifications")
    if missing:
        raise MaterialPublicationError(list(dict.fromkeys(missing)))
