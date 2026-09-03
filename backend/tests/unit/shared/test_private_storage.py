from pathlib import Path

import pytest

from src.shared.infrastructure.private_storage import FileSystemPrivateStorage


@pytest.mark.unit
def test_saves_reads_and_deletes_a_private_object(tmp_path: Path) -> None:
    storage = FileSystemPrivateStorage(tmp_path)

    size = storage.save("quote-id/file-id", [b"solid ", b"piece"])

    assert size == 11
    with storage.open("quote-id/file-id") as stream:
        assert stream.read() == b"solid piece"
    assert storage.delete("quote-id/file-id") is True
    assert storage.delete("quote-id/file-id") is False


@pytest.mark.unit
@pytest.mark.parametrize("key", ["../secret", "/absolute", "quote/../../secret", "has space"])
def test_rejects_keys_that_can_leave_private_storage(tmp_path: Path, key: str) -> None:
    storage = FileSystemPrivateStorage(tmp_path)

    with pytest.raises(ValueError, match="clave de almacenamiento"):
        storage.path_for(key)
