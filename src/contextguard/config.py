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

CONFIG_PATHS = (
    "contextguard.json",
    ".contextguard/config.json",
)


@dataclass(frozen=True)
class ContextGuardConfig:
    layer_patterns: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_LAYER_PATTERNS))
    forbidden_dependencies: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_FORBIDDEN_DEPENDENCIES))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_config() -> ContextGuardConfig:
    return ContextGuardConfig(
        layer_patterns={key: list(value) for key, value in DEFAULT_LAYER_PATTERNS.items()},
        forbidden_dependencies={key: list(value) for key, value in DEFAULT_FORBIDDEN_DEPENDENCIES.items()},
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

    return ContextGuardConfig(
        layer_patterns=layer_patterns,
        forbidden_dependencies=forbidden_dependencies,
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
