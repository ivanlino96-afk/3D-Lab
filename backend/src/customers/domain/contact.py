from __future__ import annotations

import re
from dataclasses import dataclass

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^\+?\d{10,15}$")


class ContactValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors)
        super().__init__(" ".join(errors))


def normalize_email(email: str) -> str:
    return email.strip().casefold()


@dataclass(frozen=True, slots=True)
class Contact:
    name: str
    email: str
    normalized_email: str
    phone: str

    @classmethod
    def create(cls, name: str, email: str, phone: str) -> Contact:
        clean_name = name.strip()
        clean_email = email.strip()
        clean_phone = phone.strip()
        errors: list[str] = []
        if not 2 <= len(clean_name) <= 100:
            errors.append("El nombre debe tener entre 2 y 100 caracteres.")
        if len(clean_email) > 254 or not EMAIL_PATTERN.fullmatch(clean_email):
            errors.append("El correo debe tener un formato válido.")
        if not PHONE_PATTERN.fullmatch(clean_phone):
            errors.append("El teléfono debe contener de 10 a 15 dígitos.")
        if errors:
            raise ContactValidationError(errors)
        return cls(
            name=clean_name,
            email=clean_email,
            normalized_email=normalize_email(clean_email),
            phone=clean_phone,
        )
