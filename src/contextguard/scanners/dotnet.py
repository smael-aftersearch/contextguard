from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from contextguard.config import ContextGuardConfig, default_config
from contextguard.models import (
    DependencyInfo,
    ProjectInfo,
    ScanResult,
    ViolationInfo,
    normalize_path,
)


def scan_dotnet(root: Path, config: ContextGuardConfig | None = None) -> ScanResult:
    root = root.resolve()
    config = config or default_config()

    solution_files = sorted(root.rglob("*.sln"))
    project_paths = _discover_project_paths(root, solution_files)

    projects = [_read_project(path, root, config) for path in project_paths]
    project_by_path = {Path(project.path).as_posix().lower(): project for project in projects}
    project_by_name = {project.name.lower(): project for project in projects}

    dependencies: list[DependencyInfo] = []
    violations: list[ViolationInfo] = []

    for project in projects:
        if project.layer == "unknown":
            violations.append(
                ViolationInfo(
                    rule_id="unknown-project-layer",
                    source=project.name,
                    target=project.name,
                    severity="warning",
                    message=f"{project.name} could not be mapped to a known layer.",
                )
            )

    for project in projects:
        project_dir = (root / project.path).parent
        for reference in project.project_references:
            target = _resolve_reference(reference, project_dir, root, project_by_path, project_by_name)
            target_name = target.name if target else Path(reference).stem
            target_layer = target.layer if target else "unknown"

            dependency = DependencyInfo(
                source=project.name,
                target=target_name,
                source_layer=project.layer,
                target_layer=target_layer,
            )
            dependencies.append(dependency)

            if _is_forbidden(project.layer, target_layer, config):
                violations.append(
                    ViolationInfo(
                        rule_id="layer-dependency",
                        source=project.name,
                        target=target_name,
                        message=(
                            f"{project.name} ({project.layer}) must not reference "
                            f"{target_name} ({target_layer})."
                        ),
                    )
                )

    violations.extend(_scan_source_patterns(root, projects, config))

    return ScanResult(
        root=root.as_posix(),
        solution_files=[normalize_path(path, root) for path in solution_files],
        projects=projects,
        dependencies=dependencies,
        violations=violations,
    )


def _discover_project_paths(root: Path, solution_files: list[Path]) -> list[Path]:
    projects: set[Path] = set()

    for solution in solution_files:
        projects.update(_read_solution_projects(solution, root))

    if not projects:
        projects.update(root.rglob("*.csproj"))

    return sorted(path.resolve() for path in projects if path.exists())


def _read_solution_projects(solution: Path, root: Path) -> set[Path]:
    projects: set[Path] = set()
    pattern = re.compile(r'Project\("\{[^}]+\}"\)\s*=\s*"[^"]+",\s*"([^"]+\.csproj)"', re.I)

    try:
        text = solution.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return projects

    for match in pattern.finditer(text):
        relative_path = match.group(1).replace("\\", "/")
        projects.add((solution.parent / relative_path).resolve())

    if not projects:
        projects.update(root.rglob("*.csproj"))

    return projects


def _read_project(path: Path, root: Path, config: ContextGuardConfig) -> ProjectInfo:
    package_references: list[str] = []
    project_references: list[str] = []
    target_frameworks: list[str] = []

    try:
        tree = ET.parse(path)
        xml_root = tree.getroot()
    except (ET.ParseError, OSError):
        xml_root = None

    if xml_root is not None:
        for element in xml_root.iter():
            tag = _strip_namespace(element.tag)

            if tag == "PackageReference":
                package_name = element.attrib.get("Include") or element.attrib.get("Update")
                if package_name:
                    package_references.append(package_name)

            if tag == "ProjectReference":
                include = element.attrib.get("Include")
                if include:
                    project_references.append(include)

            if tag == "TargetFramework" and element.text:
                target_frameworks.append(element.text.strip())

            if tag == "TargetFrameworks" and element.text:
                target_frameworks.extend(part.strip() for part in element.text.split(";") if part.strip())

    name = path.stem
    return ProjectInfo(
        name=name,
        path=normalize_path(path, root),
        layer=infer_layer(name, path, config),
        target_frameworks=sorted(set(target_frameworks)),
        package_references=sorted(set(package_references)),
        project_references=sorted(set(project_references)),
    )


def infer_layer(project_name: str, path: Path, config: ContextGuardConfig | None = None) -> str:
    config = config or default_config()
    value = f"{project_name} {path.as_posix()}".lower()

    for layer, patterns in config.layer_patterns.items():
        if any(pattern in value for pattern in patterns):
            return layer

    return "unknown"


def _scan_source_patterns(root: Path, projects: list[ProjectInfo], config: ContextGuardConfig) -> list[ViolationInfo]:
    violations: list[ViolationInfo] = []

    for project in projects:
        project_dir = (root / project.path).parent
        matching_rules = [rule for rule in config.forbidden_source_patterns if rule.layer == project.layer]
        if not matching_rules:
            continue

        for source_file in _iter_source_files(project_dir):
            try:
                lines = source_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue

            for line_number, line in enumerate(lines, start=1):
                for rule in matching_rules:
                    if rule.pattern in line:
                        relative_path = normalize_path(source_file, root)
                        violations.append(
                            ViolationInfo(
                                rule_id=rule.rule_id,
                                source=project.name,
                                target=f"{relative_path}:{line_number}",
                                severity=rule.severity,
                                message=f"{rule.message} Found `{rule.pattern}` in {relative_path}:{line_number}.",
                            )
                        )

    return violations


def _iter_source_files(project_dir: Path):
    ignored_parts = {"bin", "obj", ".git", ".vs"}
    for path in project_dir.rglob("*.cs"):
        if ignored_parts.intersection({part.lower() for part in path.parts}):
            continue
        yield path


def _resolve_reference(
    reference: str,
    project_dir: Path,
    root: Path,
    project_by_path: dict[str, ProjectInfo],
    project_by_name: dict[str, ProjectInfo],
) -> ProjectInfo | None:
    resolved = (project_dir / reference).resolve()
    normalized = normalize_path(resolved, root).lower()

    if normalized in project_by_path:
        return project_by_path[normalized]

    return project_by_name.get(Path(reference).stem.lower())


def _is_forbidden(source_layer: str, target_layer: str, config: ContextGuardConfig) -> bool:
    return target_layer in set(config.forbidden_dependencies.get(source_layer, []))


def _strip_namespace(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag
