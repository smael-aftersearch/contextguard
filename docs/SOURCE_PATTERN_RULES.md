# Source pattern rules

ContextGuard can validate architecture rules at two levels:

1. Project reference rules.
2. Source pattern rules.

Project reference rules answer questions such as:

```text
Can Application reference Infrastructure?
```

Source pattern rules answer questions such as:

```text
Can Application source code use Microsoft.EntityFrameworkCore?
Can WebApi source code use DbContext directly?
Can Domain source code import an infrastructure namespace?
```

## Why this matters

A project reference graph can be valid while source code still violates architecture boundaries.

For example, an Application project may not reference Infrastructure directly, but it may still contain forbidden source-level dependencies such as:

```csharp
using Microsoft.EntityFrameworkCore;
```

That kind of rule is better detected by scanning `.cs` files.

## Configuration

Source pattern rules are configured with `forbidden_source_patterns`:

```json
{
  "forbidden_source_patterns": [
    {
      "layer": "application",
      "pattern": "Microsoft.EntityFrameworkCore",
      "rule_id": "forbidden-source-pattern",
      "severity": "error",
      "message": "Application projects must not use Entity Framework Core directly."
    },
    {
      "layer": "webapi",
      "pattern": "DbContext",
      "rule_id": "forbidden-source-pattern",
      "severity": "warning",
      "message": "WebApi projects should avoid direct DbContext usage. Prefer Application services."
    }
  ]
}
```

## Default rules

The current default rules include:

- Domain must not use `Microsoft.EntityFrameworkCore`.
- Application must not use `Microsoft.EntityFrameworkCore`.
- WebApi should avoid direct `DbContext` usage. This is warning-level by default.

## Severity

Source pattern rules support two severities:

```text
error
warning
```

Error-level findings fail `contextguard validate`.
Warning-level findings are reported but do not fail validation.

## Matching behavior

The first implementation uses deterministic substring matching.

This is intentional for the MVP because it is:

- Fast.
- Predictable.
- Safe to run in CI.
- Independent from AI models.

Future versions can add regex mode or Roslyn-based analysis for C#.

## Example: ActivityGate

If `ActivityGate.Application` directly uses a concrete gRPC client namespace, a repository can add this rule:

```json
{
  "forbidden_source_patterns": [
    {
      "layer": "application",
      "pattern": "Grpc.Client",
      "severity": "error",
      "message": "Application must not use concrete gRPC clients. Define an abstraction and implement it in Infrastructure."
    }
  ]
}
```

Then run:

```powershell
python -m contextguard validate .
python -m contextguard explain .
```
