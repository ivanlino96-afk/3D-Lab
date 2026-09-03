from datetime import date

import pytest

from src.materials.domain.entities import (
    Certification,
    MaterialPropertyValue,
    PropertyDefinition,
)


@pytest.mark.unit
def test_property_formats_value_with_its_consistent_unit() -> None:
    definition = PropertyDefinition(
        slug="heat-resistance",
        name="Resistencia térmica",
        unit="°C",
    )
    property_value = MaterialPropertyValue(definition=definition, value=95, source="TDS")

    assert property_value.display_value == "95 °C"


@pytest.mark.unit
def test_property_without_value_is_explicitly_unavailable() -> None:
    definition = PropertyDefinition(slug="impact", name="Impacto", unit="kJ/m²")
    property_value = MaterialPropertyValue(definition=definition, value=None, source=None)

    assert property_value.display_value == "No disponible"


@pytest.mark.unit
def test_certification_is_public_only_with_current_evidence() -> None:
    current = Certification(
        name="Contacto alimentario",
        issuer="Laboratorio acreditado",
        evidence_url="https://example.com/certificate",
        valid_from=date(2025, 1, 1),
        valid_until=date(2027, 1, 1),
    )
    expired = Certification(
        name="Certificación expirada",
        issuer="Laboratorio acreditado",
        evidence_url="https://example.com/expired",
        valid_from=date(2023, 1, 1),
        valid_until=date(2024, 1, 1),
    )
    missing_evidence = Certification(
        name="Sin evidencia",
        issuer="Laboratorio acreditado",
        evidence_url=None,
        valid_from=date(2025, 1, 1),
        valid_until=date(2027, 1, 1),
    )

    today = date(2026, 9, 2)
    assert current.is_public(today) is True
    assert expired.is_public(today) is False
    assert missing_evidence.is_public(today) is False
