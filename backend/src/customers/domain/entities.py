from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Customer:
    id: UUID
    current_name: str
    original_email: str
    normalized_email: str
    current_phone: str
    created_at: datetime
    updated_at: datetime
