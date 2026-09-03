from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from uuid import UUID


class CostLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def label(self) -> str:
        return {self.LOW: "Bajo", self.MEDIUM: "Medio", self.HIGH: "Alto"}[self]

    @property
    def rank(self) -> int:
        return {self.LOW: 0, self.MEDIUM: 1, self.HIGH: 2}[self]


class PublicationStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    @property
    def label(self) -> str:
        return {
            self.DRAFT: "Borrador",
            self.PUBLISHED: "Publicado",
            self.ARCHIVED: "Archivado",
        }[self]


@dataclass(frozen=True, slots=True)
class Application:
    slug: str
    name: str
    factors: str


@dataclass(frozen=True, slots=True)
class PropertyDefinition:
    slug: str
    name: str
    unit: str


@dataclass(frozen=True, slots=True)
class MaterialPropertyValue:
    definition: PropertyDefinition
    value: float | None
    source: str | None

    @property
    def display_value(self) -> str:
        if self.value is None:
            return "No disponible"
        rendered = f"{self.value:g}"
        return f"{rendered} {self.definition.unit}".strip()


@dataclass(frozen=True, slots=True)
class Certification:
    name: str
    issuer: str
    evidence_url: str | None
    valid_from: date
    valid_until: date

    def is_public(self, on_date: date) -> bool:
        return bool(self.evidence_url) and self.valid_from <= on_date <= self.valid_until


@dataclass(frozen=True, slots=True)
class Material:
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
    applications: tuple[Application, ...] = field(default_factory=tuple)
    properties: tuple[MaterialPropertyValue, ...] = field(default_factory=tuple)
    certifications: tuple[Certification, ...] = field(default_factory=tuple)
    colors: tuple[str, ...] = field(default_factory=tuple)
    finishes: tuple[str, ...] = field(default_factory=tuple)

    def public_certifications(self, on_date: date) -> tuple[Certification, ...]:
        return tuple(item for item in self.certifications if item.is_public(on_date))


@dataclass(frozen=True, slots=True)
class MaterialFilters:
    applications: frozenset[str] = frozenset()
    properties: frozenset[str] = frozenset()
    availability: bool | None = None
    costs: frozenset[CostLevel] = frozenset()

    @property
    def has_preference_criteria(self) -> bool:
        return bool(self.applications or self.properties)
