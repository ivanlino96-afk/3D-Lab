import struct
from uuid import UUID

import pytest

from src.quotes.domain.uploads import (
    MAX_FILES,
    MAX_TOTAL_BYTES,
    FileLimitError,
    NoValidFilesError,
    PendingUploadsError,
    UploadItem,
    UploadSession,
    UploadStatus,
)
from src.quotes.infrastructure.stl_validator import StlValidator


def item(index: int, size: int, status: UploadStatus = UploadStatus.VALID) -> UploadItem:
    return UploadItem(
        id=UUID(int=index + 1),
        original_name=f"piece-{index}.stl",
        size_bytes=size,
        status=status,
        storage_key=f"session/{index}",
        fingerprint=f"hash-{index}",
    )


@pytest.mark.unit
def test_accepts_twenty_files_with_exact_total_limit() -> None:
    session = UploadSession(id=UUID(int=1), token="safe-token")
    size = MAX_TOTAL_BYTES // MAX_FILES

    for index in range(MAX_FILES):
        session.add(item(index, size))

    session.ensure_submittable()
    assert len(session.valid_items) == 20


@pytest.mark.unit
def test_rejects_only_the_twenty_first_file() -> None:
    session = UploadSession(id=UUID(int=1), token="safe-token")
    for index in range(MAX_FILES):
        session.add(item(index, 1))

    with pytest.raises(FileLimitError, match="20 archivos"):
        session.ensure_capacity_for(1)
    assert len(session.items) == 20


@pytest.mark.unit
def test_rejects_file_that_would_exceed_total_size() -> None:
    session = UploadSession(id=UUID(int=1), token="safe-token")
    session.add(item(1, MAX_TOTAL_BYTES))

    with pytest.raises(FileLimitError, match="500 MB"):
        session.ensure_capacity_for(1)


@pytest.mark.unit
def test_invalid_file_does_not_remove_valid_files() -> None:
    session = UploadSession(id=UUID(int=1), token="safe-token")
    session.add(item(1, 100, UploadStatus.VALID))
    session.add(item(2, 100, UploadStatus.INVALID))

    assert [uploaded.original_name for uploaded in session.valid_items] == ["piece-1.stl"]
    session.ensure_submittable()


@pytest.mark.unit
def test_can_remove_and_replace_before_submission() -> None:
    session = UploadSession(id=UUID(int=1), token="safe-token")
    session.add(item(1, 100))
    session.remove(item(1, 100).id)
    session.add(item(2, 200))

    assert [uploaded.original_name for uploaded in session.valid_items] == ["piece-2.stl"]


@pytest.mark.unit
def test_pending_upload_blocks_submission_but_keeps_completed_files() -> None:
    session = UploadSession(id=UUID(int=1), token="safe-token")
    session.add(item(1, 100, UploadStatus.VALID))
    session.add(item(2, 100, UploadStatus.PENDING))

    with pytest.raises(PendingUploadsError, match="cargas pendientes"):
        session.ensure_submittable()
    assert len(session.valid_items) == 1


@pytest.mark.unit
def test_requires_at_least_one_valid_stl() -> None:
    session = UploadSession(id=UUID(int=1), token="safe-token")
    session.add(item(1, 100, UploadStatus.INVALID))

    with pytest.raises(NoValidFilesError, match="STL válido"):
        session.ensure_submittable()


@pytest.mark.unit
def test_validates_ascii_and_binary_stl_independently(tmp_path) -> None:
    ascii_path = tmp_path / "ascii.stl"
    ascii_path.write_bytes(b"solid cube\nfacet normal 0 0 0\nendfacet\nendsolid cube")
    binary_path = tmp_path / "binary.stl"
    binary_path.write_bytes(b"binary".ljust(80, b"\0") + struct.pack("<I", 1) + bytes(50))
    validator = StlValidator()

    ascii_result = validator.validate(ascii_path, "ascii.stl")
    binary_result = validator.validate(binary_path, "binary.STL")

    assert ascii_result.is_valid is True
    assert binary_result.is_valid is True
    assert ascii_result.fingerprint != binary_result.fingerprint


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "content", "message"),
    [
        ("empty.stl", b"", "vacío"),
        ("wrong.obj", b"solid x\nendsolid x", "extensión"),
        ("broken.stl", b"not an stl", "dañado"),
    ],
)
def test_rejects_invalid_stl_with_recoverable_spanish_error(
    tmp_path, name: str, content: bytes, message: str
) -> None:
    path = tmp_path / name
    path.write_bytes(content)

    result = StlValidator().validate(path, name)

    assert result.is_valid is False
    assert message in result.error_message
