from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Service:
    id: UUID
    slug: str
    name: str
    summary: str
    description: str
    display_order: int
    is_published: bool
