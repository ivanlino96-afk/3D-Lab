from __future__ import annotations

from dataclasses import dataclass

from src.materials.domain.entities import Material, MaterialFilters, PublicationStatus


@dataclass(frozen=True, slots=True)
class MaterialMatch:
    material: Material
    matched_count: int
    reasons: tuple[str, ...]


def rank_materials(
    materials: list[Material],
    filters: MaterialFilters,
) -> list[MaterialMatch]:
    matches: list[MaterialMatch] = []
    for material in materials:
        if material.status is not PublicationStatus.PUBLISHED:
            continue
        if filters.availability is not None and material.available is not filters.availability:
            continue
        if filters.costs and material.cost_level not in filters.costs:
            continue

        application_names = {item.slug: item.name for item in material.applications}
        property_names = {
            item.definition.slug: item.definition.name for item in material.properties
        }
        reasons = [
            f"Aplicación: {application_names[slug]}"
            for slug in filters.applications
            if slug in application_names
        ]
        reasons.extend(
            f"Propiedad: {property_names[slug]}"
            for slug in filters.properties
            if slug in property_names
        )
        if filters.has_preference_criteria and not reasons:
            continue

        matches.append(
            MaterialMatch(
                material=material,
                matched_count=len(reasons),
                reasons=tuple(sorted(reasons)),
            )
        )

    return sorted(
        matches,
        key=lambda match: (
            -match.matched_count,
            not match.material.available,
            match.material.cost_level.rank,
            match.material.display_order,
            match.material.name.casefold(),
        ),
    )
