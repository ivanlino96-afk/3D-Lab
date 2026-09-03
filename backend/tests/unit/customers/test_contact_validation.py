import pytest

from src.customers.domain.contact import Contact, ContactValidationError, normalize_email


@pytest.mark.unit
def test_accepts_contact_without_account_and_normalizes_email() -> None:
    contact = Contact.create("  Ana López  ", " ANA@Example.COM ", "+525512345678")

    assert contact.name == "Ana López"
    assert contact.email == "ANA@Example.COM"
    assert contact.normalized_email == "ana@example.com"
    assert contact.phone == "+525512345678"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "email", "phone", "field"),
    [
        ("A", "ana@example.com", "5512345678", "nombre"),
        ("Ana", "invalid", "5512345678", "correo"),
        ("Ana", "ana@example.com", "55-1234", "teléfono"),
    ],
)
def test_rejects_invalid_contact_with_spanish_field_error(
    name: str, email: str, phone: str, field: str
) -> None:
    with pytest.raises(ContactValidationError, match=field):
        Contact.create(name, email, phone)


@pytest.mark.unit
def test_email_identity_is_case_and_space_insensitive() -> None:
    assert normalize_email(" Client@Example.COM ") == "client@example.com"
