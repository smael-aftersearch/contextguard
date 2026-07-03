# ContextGuard

ContextGuard turns a codebase into clear development rules for humans, AI agents, and CI pipelines.

The goal is not only to generate documentation. The goal is to discover how a project is built, write that knowledge as AI-ready context, and then enforce the important rules so future changes cannot silently break the architecture.

## What ContextGuard does

ContextGuard will analyze a repository and generate:

- AI context files that explain the project structure, conventions, and rules.
- Architecture rules that describe what is allowed and what is forbidden.
- Validation checks that can run locally or in CI.
- Optional pipeline templates to prevent rule violations from being merged.

## Initial focus

The first version focuses on .NET / C# projects, especially Clean Architecture style solutions.

The first supported rules include:

- Detecting projects inside a `.sln` or folder.
- Reading `.csproj` references and package references.
- Inferring common layers such as Domain, Application, Infrastructure, WebApi, and Tests.
- Detecting invalid layer dependencies.
- Generating AI-ready rule files.
- Reading repository-specific rules from `.contextguard/config.json`.

## Install locally

```bash
git clone https://github.com/smael-aftersearch/contextguard.git
cd contextguard
python -m pip install -e .
```

On Windows PowerShell, using a virtual environment is recommended:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m contextguard analyze .
```

If PowerShell blocks activation, run this command once for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the virtual environment again.

## Usage

Analyze a repository:

```bash
contextguard analyze /path/to/repo
```

If the `contextguard` command is not available in your terminal, use the module form:

```bash
python -m contextguard analyze /path/to/repo
```

Print the full report as JSON:

```bash
python -m contextguard analyze /path/to/repo --json
```

Generate initial ContextGuard files in a repository:

```bash
python -m contextguard init /path/to/repo
```

Validate architecture rules:

```bash
python -m contextguard validate /path/to/repo
```

## Generated files

The `init` command currently generates:

```text
.contextguard/config.json
.contextguard/context.json
.ai/rules.md
```

## Configuration

ContextGuard looks for config in this order:

```text
contextguard.json
.contextguard/config.json
```

Example config:

```json
{
  "layer_patterns": {
    "domain": ["domain"],
    "application": ["application"],
    "infrastructure": ["infrastructure", ".infra", "/infra"],
    "webapi": ["webapi", "endpoint", "endpoints", ".api", "/api"],
    "tests": ["test", "tests", "spec"]
  },
  "forbidden_dependencies": {
    "domain": ["application", "infrastructure", "webapi", "tests"],
    "application": ["infrastructure", "webapi", "tests"],
    "infrastructure": ["webapi", "tests"],
    "webapi": ["tests"]
  }
}
```

## Test ContextGuard itself

```bash
python -m pip install -e .
python -m unittest discover -s tests
python -m contextguard analyze .
```

## Test against a .NET repository

```bash
python -m contextguard analyze D:/Source/MyDotnetRepo
python -m contextguard init D:/Source/MyDotnetRepo
python -m contextguard validate D:/Source/MyDotnetRepo
```

Expected validation behavior:

- Exit code `0` means no architecture violations were detected.
- Exit code `1` means at least one violation was detected.
- Exit code `2` means ContextGuard could not read the config.

## MVP plan

The .NET MVP task list is tracked in `docs/MVP_DOTNET.md`.

## Product vision

ContextGuard should become a lightweight governance layer for AI-assisted development.

Instead of asking an AI agent to read the entire repository every time, ContextGuard gives it a compact, accurate, and enforceable project contract.

## Current status

Early MVP. The first milestone is a Python CLI that can scan a .NET solution and produce a simple architecture report.

## Tagline

Generate AI context. Enforce codebase rules.
