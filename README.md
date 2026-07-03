# ContextGuard

ContextGuard turns a codebase into clear development rules for humans, AI agents, and CI pipelines.

The goal is not only to generate documentation. The goal is to discover how a project is built, write that knowledge as AI-ready context, and then enforce the important rules so future changes cannot silently break the architecture.

## What ContextGuard does

ContextGuard will analyze a repository and generate:

- AI context files that explain the project structure, conventions, and rules.
- Architecture rules that describe what is allowed and what is forbidden.
- Validation checks that can run locally or in CI.
- Explanations for findings, including why they matter and how to fix them.
- Optional pipeline templates to prevent rule violations from being merged.

## Initial focus

The first version focuses on .NET / C# projects, especially Clean Architecture style solutions.

The first supported rules include:

- Detecting projects inside a `.sln` or folder.
- Reading `.csproj` references and package references.
- Inferring common layers such as Domain, Application, Infrastructure, WebApi, and Tests.
- Detecting invalid layer dependencies.
- Scanning `.cs` files for forbidden source patterns.
- Filtering source pattern rules by include/exclude path patterns.
- Limiting noisy legacy findings with `max_findings_per_project`.
- Explaining detected findings with practical fix guidance.
- Generating AI-ready rule files.
- Generating a GitHub Actions workflow for validation.
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

Show project dependencies in the text report:

```bash
python -m contextguard analyze /path/to/repo --show-deps
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

Explain detected findings:

```bash
python -m contextguard explain /path/to/repo
```

Explain a specific rule:

```bash
python -m contextguard explain . --rule layer-dependency
python -m contextguard explain . --rule forbidden-source-pattern
```

Generate a GitHub Actions workflow in the target repository:

```bash
python -m contextguard generate-ci /path/to/repo
```

## Generated files

The `init` command currently generates:

```text
.contextguard/config.json
.contextguard/context.json
.ai/rules.md
```

The `generate-ci` command generates:

```text
.github/workflows/contextguard.yml
```

The generated `.ai/rules.md` includes detected projects, architecture rules, detected dependencies, current findings, and development instructions for AI-assisted coding.

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
  },
  "forbidden_source_patterns": [
    {
      "layer": "application",
      "pattern": "Microsoft.EntityFrameworkCore",
      "severity": "warning",
      "match_type": "contains",
      "include": ["**/*.cs"],
      "exclude": ["**/Generated/**", "**/*.g.cs"],
      "max_findings_per_project": 5,
      "message": "Application currently uses EF Core. Prefer abstractions or move data access to Infrastructure over time."
    },
    {
      "layer": "application",
      "pattern": "using\\s+Grpc\\.Client",
      "severity": "error",
      "match_type": "regex",
      "message": "Application must not use concrete gRPC clients. Define an abstraction and implement it in Infrastructure."
    },
    {
      "layer": "webapi",
      "pattern": "DbContext",
      "severity": "warning",
      "message": "WebApi projects should avoid direct DbContext usage. Prefer Application services."
    }
  ]
}
```

See `docs/SOURCE_PATTERN_RULES.md` for more details.

## Test ContextGuard itself

```bash
python -m pip install -e .
python -m unittest discover -s tests
python -m contextguard analyze .
```

## Test against a .NET repository

```bash
python -m contextguard analyze D:/Source/MyDotnetRepo --show-deps
python -m contextguard init D:/Source/MyDotnetRepo
python -m contextguard validate D:/Source/MyDotnetRepo
python -m contextguard explain D:/Source/MyDotnetRepo
python -m contextguard generate-ci D:/Source/MyDotnetRepo
```

Expected validation behavior:

- Exit code `0` means no error-level architecture violations were detected.
- Exit code `1` means at least one error-level violation was detected.
- Exit code `2` means ContextGuard could not read the config.
- Warning-level findings do not fail validation.

## Real example

The first real tested finding is documented in `docs/ACTIVITYGATE_EXAMPLE.md`.

## MVP plan

The .NET MVP task list is tracked in `docs/MVP_DOTNET.md`.

## Product vision

ContextGuard should become a lightweight governance layer for AI-assisted development.

Instead of asking an AI agent to read the entire repository every time, ContextGuard gives it a compact, accurate, and enforceable project contract.

## Current status

Early MVP. The first milestone is a Python CLI that can scan a .NET solution and produce a simple architecture report.

## Tagline

Generate AI context. Enforce codebase rules.
