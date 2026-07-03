from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProjectInfo:
    name: str
    path: str
    layer: str
    target_frameworks: list[str] = field(default_factory=list)
    package_references: list[str] = field(default_factory=list)
    project_references: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DependencyInfo:
    source: str
    target: str
    source_layer: str
    target_layer: str


@dataclass(frozen=True)
class ViolationInfo:
    rule_id: str
    message: str
    source: str
    target: str
    severity: str = "error"


@dataclass(frozen=True)
class ScanResult:
    root: str
    solution_files: list[str]
    projects: list[ProjectInfo]
    dependencies: list[DependencyInfo]
    violations: list[ViolationInfo]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


def normalize_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()
