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

## Install locally

```bash
git clone https://github.com/smael-aftersearch/contextguard.git
cd contextguard
python -m pip install -e .
```

## Usage

Analyze a repository:

```bash
contextguard analyze /path/to/repo
```

Print the full report as JSON:

```bash
contextguard analyze /path/to/repo --json
```

Generate initial ContextGuard files in a repository:

```bash
contextguard init /path/to/repo
```

Validate architecture rules:

```bash
contextguard validate /path/to/repo
```

## Generated files

The `init` command currently generates:

```text
.contextguard/context.json
.ai/rules.md
```

## Product vision

ContextGuard should become a lightweight governance layer for AI-assisted development.

Instead of asking an AI agent to read the entire repository every time, ContextGuard gives it a compact, accurate, and enforceable project contract.

## Current status

Early MVP. The first milestone is a Python CLI that can scan a .NET solution and produce a simple architecture report.

## Tagline

Generate AI context. Enforce codebase rules.
