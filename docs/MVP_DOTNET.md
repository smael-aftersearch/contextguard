# ContextGuard .NET MVP Plan

This document tracks the first version of ContextGuard for .NET / C# repositories.

## MVP goal

Build a Python CLI that can scan a .NET solution, infer the basic architecture, generate AI-ready project rules, validate important architecture constraints locally or in CI, and explain detected findings with practical fix guidance.

## Target users

- Developers working on .NET monoliths or modular services.
- Teams using Clean Architecture, layered architecture, or similar project structures.
- Teams using AI coding tools that need compact and reliable project context.

## Version 1 scope

### 1. Repository discovery

Status: done

ContextGuard should find:

- `.sln` files.
- `.csproj` files.
- Projects referenced from a solution.
- Projects found directly in a folder when no solution exists.

### 2. .NET project scanning

Status: done

ContextGuard should read from `.csproj` files:

- Project name.
- Target framework or target frameworks.
- Package references.
- Project references.

### 3. Layer inference

Status: done for basic MVP

ContextGuard can infer common layers such as:

- Domain
- Application
- Infrastructure
- WebApi
- Tests
- Unknown

The default implementation uses project names and paths. Layer patterns are now configurable through `.contextguard/config.json`.

### 4. Project reference architecture rules

Status: done for basic MVP

ContextGuard validates layer dependency rules.

Default rules:

- Domain must not reference Application, Infrastructure, WebApi, or Tests.
- Application must not reference Infrastructure, WebApi, or Tests.
- Infrastructure must not reference WebApi or Tests.
- WebApi must not reference Tests.

These rules are configurable through `.contextguard/config.json`.

### 5. Source pattern architecture rules

Status: improved basic version done

ContextGuard can scan `.cs` source files and report forbidden text patterns per layer.

Current capabilities:

- `contains` matching.
- `regex` matching.
- `include` path filters.
- `exclude` path filters.
- `max_findings_per_project` for noisy legacy codebases.
- Error and warning severities.

Default examples:

- Domain must not use `Microsoft.EntityFrameworkCore`.
- Application must not use `Microsoft.EntityFrameworkCore`.
- WebApi should avoid direct `DbContext` usage. This is warning-level by default.

Source pattern rules are configured through `forbidden_source_patterns` in `.contextguard/config.json`.

Next steps:

- Add grouped summary output for repeated findings.
- Add Roslyn-based C# analysis in a later version.

### 6. AI context generation

Status: improved basic version done

The `init` command currently generates:

- `.contextguard/config.json`
- `.contextguard/context.json`
- `.ai/rules.md`

The generated AI rules now include:

- Detected projects.
- Architecture rules.
- Detected project dependencies.
- Current findings.
- Development instructions.

Next steps:

- Add better explanations for detected conventions.
- Add project examples.
- Add generated task guidance for AI agents.

### 7. Validation command

Status: improved basic version done

The `validate` command returns a non-zero exit code only when error-level architecture findings are detected.

Current behavior:

- Error findings fail validation.
- Warning findings do not fail validation.
- Unknown layers are reported as warnings.

Next steps:

- Add rule IDs and severity levels directly from dependency config.
- Add more warning-only rules.

### 8. Explain command

Status: improved basic version done

The `explain` command explains detected findings and specific rules.

Examples:

```bash
python -m contextguard explain .
python -m contextguard explain . --rule layer-dependency
python -m contextguard explain . --rule forbidden-source-pattern
```

### 9. CI integration

Status: basic generator done

ContextGuard can generate a GitHub Actions workflow for target repositories:

```bash
python -m contextguard generate-ci .
```

The generated workflow runs:

```bash
python -m contextguard validate .
```

Next steps:

- Add Azure Pipelines template support.
- Allow choosing package source/version for CI installation.

## What is intentionally out of scope for v1

- Deep C# AST parsing.
- Full business logic detection.
- Automatic code rewriting.
- Multi-language support.
- Cloud dashboard.
- AI-based rule generation inside CI.

## How to test the MVP manually

From the ContextGuard repository:

```bash
python -m pip install -e .
python -m unittest discover -s tests
python -m contextguard analyze .
```

Against a real .NET repository:

```bash
python -m contextguard analyze /path/to/dotnet-repo --show-deps
python -m contextguard analyze /path/to/dotnet-repo --json
python -m contextguard init /path/to/dotnet-repo
python -m contextguard validate /path/to/dotnet-repo
python -m contextguard explain /path/to/dotnet-repo
python -m contextguard generate-ci /path/to/dotnet-repo
```

Expected behavior:

- `analyze` prints the detected solutions, projects, dependencies, errors, warnings, and findings.
- `init` creates ContextGuard output files.
- `validate` exits with code `0` when there are no error-level findings.
- `validate` exits with code `1` when invalid error-level dependencies are found.
- `validate` exits with code `2` when the config cannot be read.
- `explain` prints why a finding matters and how to fix it.
- `generate-ci` writes `.github/workflows/contextguard.yml`.

## Current next priorities

1. Add grouped summary output for repeated findings.
2. Generate Azure Pipelines template support.
3. Improve `.ai/rules.md` with richer detected conventions.
4. Add tests for CLI command behavior.
5. Add package publishing workflow.
