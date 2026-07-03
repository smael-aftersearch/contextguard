# ContextGuard .NET MVP Plan

This document tracks the first version of ContextGuard for .NET / C# repositories.

## MVP goal

Build a Python CLI that can scan a .NET solution, infer the basic architecture, generate AI-ready project rules, and validate important architecture constraints locally or in CI.

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

### 4. Architecture rules

Status: done for basic MVP

ContextGuard validates layer dependency rules.

Default rules:

- Domain must not reference Application, Infrastructure, WebApi, or Tests.
- Application must not reference Infrastructure, WebApi, or Tests.
- Infrastructure must not reference WebApi or Tests.
- WebApi must not reference Tests.

These rules are now configurable through `.contextguard/config.json`.

### 5. AI context generation

Status: basic version done

The `init` command currently generates:

- `.contextguard/config.json`
- `.contextguard/context.json`
- `.ai/rules.md`

Next steps:

- Add better explanations for detected conventions.
- Add project examples.
- Add generated task guidance for AI agents.

### 6. Validation command

Status: basic version done

The `validate` command returns a non-zero exit code when architecture violations are detected.

Next steps:

- Add better output formatting.
- Add rule IDs and severity levels from config.
- Add warning-only rules.

### 7. CI integration

Status: basic version done

A GitHub Actions workflow currently runs unit tests and a CLI smoke test.

Next steps:

- Generate a pipeline template for target repositories.
- Document how to add `contextguard validate` to a .NET repository pipeline.

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
contextguard analyze .
```

Against a real .NET repository:

```bash
contextguard analyze /path/to/dotnet-repo
contextguard analyze /path/to/dotnet-repo --json
contextguard init /path/to/dotnet-repo
contextguard validate /path/to/dotnet-repo
```

Expected behavior:

- `analyze` prints the detected solutions, projects, dependencies, and violations.
- `init` creates ContextGuard output files.
- `validate` exits with code `0` when there are no violations.
- `validate` exits with code `1` when invalid layer dependencies are found.
- `validate` exits with code `2` when the config cannot be read.

## Current next priorities

1. Add severity levels to rules.
2. Add warning-only rules.
3. Add source-pattern rules, for example forbidding `DbContext` inside controllers.
4. Generate a CI pipeline template for target .NET repositories.
5. Improve `.ai/rules.md` with richer detected conventions.
