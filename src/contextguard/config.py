from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_LAYER_PATTERNS: dict[str, list[str]] = {
    "tests": ["test", "tests", "spec"],
    "domain": ["domain"],
    "application": ["application"],
    "infrastructure": ["infrastructure", ".infra", "/infra"],
    "webapi": ["webapi", "endpoint", "endpoints", ".api", "/api"],
}

DEFAULT_FORBIDDEN_DEPENDENCIES: dict[str, list[str]] = {
    "domain": ["application", "infrastructure", "webapi", "tests"],
    "application": ["infrastructure", "webapi", "tests"],
    "infrastructure": ["webapi", "tests"],
    "webapi": ["tests"],
}

DEFAULT_FORBIDDEN_SOURCE_PATTERNS: list[dict[str, Any]] = [
    {
        "layer": "domain",
        "pattern": "Microsoft.EntityFrameworkCore",
        "rule_id": "forbidden-source-pattern",
        "severity": "error",
        "message": "Domain projects must not use Entity Framework Core directly.",
    },
    {
        "layer": "application",
        "pattern": "Microsoft.EntityFrameworkCore",
        "rule_id": "forbidden-source-pattern",
        "severity": "error",
        "message": "Application projects must not use Entity Framework Core directly.",
    },
    {
        "layer": "webapi",
        "pattern": "DbContext",
        "rule_id": "forbidden-source-pattern",
        "severity": "warning",
        "message": "WebApi projects should avoid direct DbContext usage. Prefer Application services.",
    },
]

CONFIG_PATHS = (
    "contextguard.json",
    ".contextguard/config.json",
)


@dataclass(frozen=True)
class SourcePatternRule:
    layer: str
    pattern: str
    message: str
    rule_id: str = "forbidden-source-pattern"
    severity: str = "error"
    match_type: str = "contains"
    include: list[str] = field(default_factory=lambda: ["**/*.cs"])
    exclude: list[str] = field(default_factory=list)
    max_findings_per_project: int | None = None

    def normalized(self) -> "SourcePatternRule":
        return SourcePatternRule(
            layer=self.layer.lower(),
            pattern=self.pattern,
            message=self.message,
            rule_id=self.rule_id,
            severity=self.severity.lower(),
            match_type=self.match_type.lower(),
            include=list(self.include),
            exclude=list(self.exclude),
            max_findings_per_project=self.max_findings_per_project,
        )


@dataclass(frozen=True)
class ContextGuardConfig:
    layer_patterns: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_LAYER_PATTERNS))
    forbidden_dependencies: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_FORBIDDEN_DEPENDENCIES))
    forbidden_source_patterns: list[SourcePatternRule] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_config() -> ContextGuardConfig:
    return ContextGuardConfig(
        layer_patterns={key: list(value) for key, value in DEFAULT_LAYER_PATTERNS.items()},
        forbidden_dependencies={key: list(value) for key, value in DEFAULT_FORBIDDEN_DEPENDENCIES.items()},
        forbidden_source_patterns=[_source_pattern_rule_from_dict(item) for item in DEFAULT_FORBIDDEN_SOURCE_PATTERNS],
    )


def load_config(root: Path) -> ContextGuardConfig:
    root = root.resolve()

    for relative_path in CONFIG_PATHS:
        candidate = root / relative_path
        if candidate.exists():
            return _read_config_file(candidate)

    return default_config()


def _read_config_file(path: Path) -> ContextGuardConfig:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid ContextGuard config JSON: {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"ContextGuard config must be a JSON object: {path}")

    base = default_config()
    layer_patterns = _read_string_list_map(raw.get("layer_patterns"), base.layer_patterns, "layer_patterns")
    forbidden_dependencies = _read_string_list_map(
        raw.get("forbidden_dependencies"),
        base.forbidden_dependencies,
        "forbidden_dependencies",
    )
    forbidden_source_patterns = _read_source_pattern_rules(
        raw.get("forbidden_source_patterns"),
        base.forbidden_source_patterns,
    )

    return ContextGuardConfig(
        layer_patterns=layer_patterns,
        forbidden_dependencies=forbidden_dependencies,
        forbidden_source_patterns=forbidden_source_patterns,
    )


def _read_string_list_map(value: Any, fallback: dict[str, list[str]], field_name: str) -> dict[str, list[str]]:
    if value is None:
        return {key: list(items) for key, items in fallback.items()}

    if not isinstance(value, dict):
        raise ValueError(f"Config field `{field_name}` must be an object.")

    result: dict[str, list[str]] = {}
    for key, items in value.items():
        if not isinstance(key, str):
            raise ValueError(f"Config field `{field_name}` contains a non-string key.")
        if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
            raise ValueError(f"Config field `{field_name}.{key}` must be a list of strings.")
        result[key.lower()] = [item.lower() for item in items]

    return result


def _read_source_pattern_rules(value: Any, fallback: list[SourcePatternRule]) -> list[SourcePatternRule]:
    if value is None:
        return list(fallback)

    if not isinstance(value, list):
        raise ValueError("Config field `forbidden_source_patterns` must be a list.")

    return [_source_pattern_rule_from_dict(item) for item in value]


def _source_pattern_rule_from_dict(value: Any) -> SourcePatternRule:
    if not isinstance(value, dict):
        raise ValueError("Each forbidden source pattern rule must be an object.")

    layer = value.get("layer")
    pattern = value.get("pattern")
    message = value.get("message")
    rule_id = value.get("rule_id", "forbidden-source-pattern")
    severity = value.get("severity", "error")
    match_type = value.get("match_type", "contains")
    include = _read_string_list(value.get("include"), ["**/*.cs"], "include")
    exclude = _read_string_list(value.get("exclude"), [], "exclude")
    max_findings_per_project = value.get("max_findings_per_project")

    if not all(isinstance(item, str) and item.strip() for item in (layer, pattern, message, rule_id, severity, match_type)):
        raise ValueError("Source pattern rules require string values for layer, pattern, message, rule_id, severity, and match_type.")

    if severity.lower() not in {"error", "warning"}:
        raise ValueError("Source pattern rule severity must be either `error` or `warning`.")

    if match_type.lower() not in {"contains", "regex"}:
        raise ValueError("Source pattern rule match_type must be either `contains` or `regex`.")

    if max_findings_per_project is not None:
        if not isinstance(max_findings_per_project, int) or max_findings_per_project < 1:
            raise ValueError("Source pattern rule max_findings_per_project must be a positive integer.")

    return SourcePatternRule(
        layer=layer.lower(),
        pattern=pattern,
        message=message,
        rule_id=rule_id,
        severity=severity.lower(),
        match_type=match_type.lower(),
        include=include,
        exclude=exclude,
        max_findings_per_project=max_findings_per_project,
    )


def _read_string_list(value: Any, fallback: list[str], field_name: str) -> list[str]:
    if value is None:
        return list(fallback)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Source pattern rule `{field_name}` must be a list of strings.")
    return list(value)
