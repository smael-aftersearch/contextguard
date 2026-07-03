from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from contextguard.config import ContextGuardConfig, default_config, load_config
from contextguard.scanners.dotnet import scan_dotnet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="contextguard",
        description="Generate codebase context and enforce architecture rules.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a codebase and print a report.")
    analyze_parser.add_argument("path", nargs="?", default=".", help="Repository path. Defaults to current directory.")
    analyze_parser.add_argument("--json", action="store_true", help="Print the full report as JSON.")
    analyze_parser.add_argument("--show-deps", action="store_true", help="Print project references in the text report.")

    init_parser = subparsers.add_parser("init", help="Generate initial ContextGuard files.")
    init_parser.add_argument("path", nargs="?", default=".", help="Repository path. Defaults to current directory.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite generated files if they already exist.")

    validate_parser = subparsers.add_parser("validate", help="Validate architecture rules.")
    validate_parser.add_argument("path", nargs="?", default=".", help="Repository path. Defaults to current directory.")
    validate_parser.add_argument("--json", action="store_true", help="Print validation report as JSON.")

    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            return _analyze(Path(args.path), as_json=args.json, show_deps=args.show_deps)
        if args.command == "init":
            return _init(Path(args.path), force=args.force)
        if args.command == "validate":
            return _validate(Path(args.path), as_json=args.json)
    except ValueError as exc:
        print(f"ContextGuard error: {exc}")
        return 2

    parser.print_help()
    return 1


def _analyze(root: Path, as_json: bool, show_deps: bool) -> int:
    config = load_config(root)
    result = scan_dotnet(root, config=config)
    if as_json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        _print_summary(result.to_dict(), show_deps=show_deps)
    return 0


def _init(root: Path, force: bool) -> int:
    root = root.resolve()
    context_dir = root / ".contextguard"
    ai_dir = root / ".ai"
    config_file = context_dir / "config.json"
    context_file = context_dir / "context.json"
    rules_file = ai_dir / "rules.md"

    for path in (context_file, rules_file):
        if path.exists() and not force:
            print(f"File already exists: {path}")
            print("Use --force to overwrite generated files.")
            return 1

    context_dir.mkdir(parents=True, exist_ok=True)
    ai_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(root) if config_file.exists() else default_config()
    result = scan_dotnet(root, config=config)

    if force or not config_file.exists():
        config_file.write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    context_file.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    rules_file.write_text(_build_ai_rules(result.to_dict(), config), encoding="utf-8")

    print("ContextGuard initialized.")
    print(f"- {config_file.relative_to(root)}")
    print(f"- {context_file.relative_to(root)}")
    print(f"- {rules_file.relative_to(root)}")
    if result.has_violations:
        print(f"\nDetected {len(result.violations)} finding(s). Run `contextguard validate` for details.")
    return 0


def _validate(root: Path, as_json: bool) -> int:
    config = load_config(root)
    result = scan_dotnet(root, config=config)
    if as_json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    elif not result.violations:
        print("ContextGuard validation passed. No architecture findings found.")
    else:
        print(
            "ContextGuard validation completed: "
            f"{result.error_count} error(s), {result.warning_count} warning(s).\n"
        )
        for violation in result.violations:
            print(f"[{violation.severity}] {violation.rule_id}: {violation.message}")
    return 1 if result.has_errors else 0


def _print_summary(report: dict, show_deps: bool = False) -> None:
    error_count = len([item for item in report["violations"] if item["severity"] == "error"])
    warning_count = len([item for item in report["violations"] if item["severity"] == "warning"])

    print("ContextGuard analysis")
    print("=====================")
    print(f"Root: {report['root']}")
    print(f"Solutions: {len(report['solution_files'])}")
    print(f"Projects: {len(report['projects'])}")
    print(f"Dependencies: {len(report['dependencies'])}")
    print(f"Errors: {error_count}")
    print(f"Warnings: {warning_count}")

    if report["projects"]:
        print("\nProjects:")
        for project in report["projects"]:
            frameworks = ", ".join(project["target_frameworks"]) or "unknown framework"
            print(f"- {project['name']} [{project['layer']}] ({frameworks})")

    if show_deps and report["dependencies"]:
        print("\nDependencies:")
        for dependency in report["dependencies"]:
            print(
                f"- {dependency['source']} [{dependency['source_layer']}] -> "
                f"{dependency['target']} [{dependency['target_layer']}]"
            )

    if report["violations"]:
        print("\nFindings:")
        for violation in report["violations"]:
            print(f"- [{violation['severity']}] {violation['message']}")


def _build_ai_rules(report: dict, config: ContextGuardConfig) -> str:
    lines = [
        "# ContextGuard AI Rules",
        "",
        "This file is generated by ContextGuard. It describes the detected project structure and rules.",
        "",
        "## Detected projects",
        "",
    ]

    if not report["projects"]:
        lines.append("No .NET projects were detected yet.")
    else:
        lines.append("| Project | Layer | Target frameworks |")
        lines.append("|---|---|---|")
        for project in report["projects"]:
            frameworks = ", ".join(project["target_frameworks"]) or "unknown"
            lines.append(f"| `{project['name']}` | `{project['layer']}` | {frameworks} |")

    lines.extend(["", "## Architecture rules", ""])
    for source_layer, forbidden_layers in config.forbidden_dependencies.items():
        if forbidden_layers:
            formatted = ", ".join(f"`{layer}`" for layer in forbidden_layers)
            lines.append(f"- `{source_layer}` projects must not reference {formatted} projects.")

    lines.extend([
        "- Use abstractions from inner layers instead of referencing outer layers directly.",
        "",
        "## Development instructions",
        "",
        "1. Keep business rules in the inner layers.",
        "2. Do not introduce dependencies from inner layers to outer layers.",
        "3. Prefer existing project conventions over new patterns.",
        "4. Add new files to the layer that matches their responsibility.",
        "5. Run `contextguard validate` before considering the change complete.",
        "",
    ])

    if report["violations"]:
        lines.extend(["## Current findings", ""])
        for violation in report["violations"]:
            lines.append(f"- `{violation['severity']}` `{violation['rule_id']}`: {violation['message']}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
