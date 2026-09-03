import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_domain_does_not_import_frameworks_or_infrastructure() -> None:
    forbidden_prefixes = ("fastapi", "sqlalchemy", "starlette")
    violations: list[str] = []

    for path in SOURCE_ROOT.glob("*/domain/*.py"):
        for module in imported_modules(path):
            if module.startswith(forbidden_prefixes) or ".infrastructure" in module:
                violations.append(f"{path.relative_to(SOURCE_ROOT)} -> {module}")

    assert violations == []


def test_presentation_does_not_import_database_session_factory() -> None:
    violations: list[str] = []
    for path in SOURCE_ROOT.glob("*/presentation/*.py"):
        source = path.read_text(encoding="utf-8")
        if "SessionFactory" in source or ".commit(" in source or ".rollback(" in source:
            violations.append(str(path.relative_to(SOURCE_ROOT)))

    assert violations == []
