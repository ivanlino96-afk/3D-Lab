from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StlValidationResult:
    is_valid: bool
    fingerprint: str
    error_message: str | None = None


class StlValidator:
    def validate(self, path: Path, original_name: str) -> StlValidationResult:
        fingerprint = self._fingerprint(path)
        if Path(original_name).suffix.casefold() != ".stl":
            return StlValidationResult(False, fingerprint, "El archivo debe tener extensión STL.")
        size = path.stat().st_size
        if size == 0:
            return StlValidationResult(False, fingerprint, "El archivo STL está vacío.")
        if self._is_ascii_stl(path) or self._is_binary_stl(path, size):
            return StlValidationResult(True, fingerprint)
        return StlValidationResult(
            False,
            fingerprint,
            "El archivo STL está dañado o no contiene una geometría reconocible.",
        )

    @staticmethod
    def _fingerprint(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _is_ascii_stl(path: Path) -> bool:
        with path.open("rb") as stream:
            beginning = stream.read(4096).lstrip().lower()
            if not beginning.startswith(b"solid") or b"facet" not in beginning:
                return False
            stream.seek(max(0, path.stat().st_size - 4096))
            ending = stream.read().rstrip().lower()
            return b"endsolid" in ending

    @staticmethod
    def _is_binary_stl(path: Path, size: int) -> bool:
        if size < 84:
            return False
        with path.open("rb") as stream:
            stream.seek(80)
            triangle_count = struct.unpack("<I", stream.read(4))[0]
        expected_size = 84 + triangle_count * 50
        return triangle_count > 0 and expected_size <= size
