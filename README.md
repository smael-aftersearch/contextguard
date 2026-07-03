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

The first supported rules will include:

- Detecting projects inside a `.sln` or folder.
- Reading `.csproj` references and package references.
- Inferring common layers such as Domain, Application, Infrastructure, WebApi, and Tests.
- Detecting invalid layer dependencies.
- Generating AI-ready rule files.

## Product vision

ContextGuard should become a lightweight governance layer for AI-assisted development.

Instead of asking an AI agent to read the entire repository every time, ContextGuard gives it a compact, accurate, and enforceable project contract.

## Planned CLI

```bash
contextguard analyze
contextguard init
contextguard validate
contextguard generate
```

## Current status

Early MVP. The first milestone is a Python CLI that can scan a .NET solution and produce a simple architecture report.

## Tagline

Generate AI context. Enforce codebase rules.
