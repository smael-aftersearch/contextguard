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
      "match_type": "contains",
      "include": ["**/*.cs"],
      "exclude": ["**/Generated/**", "**/*.g.cs"],
      "max_findings_per_project": 10,
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

## Rule fields

| Field | Required | Default | Description |
|---|---:|---|---|
| `layer` | yes | | Layer where the rule applies. |
| `pattern` | yes | | Text or regex pattern to find. |
| `message` | yes | | Finding message shown to the user. |
| `rule_id` | no | `forbidden-source-pattern` | Rule identifier. |
| `severity` | no | `error` | Either `error` or `warning`. |
| `match_type` | no | `contains` | Either `contains` or `regex`. |
| `include` | no | `["**/*.cs"]` | File path patterns to include. |
| `exclude` | no | `[]` | File path patterns to exclude. |
| `max_findings_per_project` | no | unlimited | Maximum findings for this rule per project. |

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

The default matching behavior is deterministic substring matching:

```json
{
  "match_type": "contains"
}
```

Regex matching is also supported:

```json
{
  "match_type": "regex",
  "pattern": "using\\s+Grpc\\.Client"
}
```

The MVP keeps matching deterministic because it is:

- Fast.
- Predictable.
- Safe to run in CI.
- Independent from AI models.

Future versions can add Roslyn-based analysis for C#.

## Managing noisy legacy findings

Some existing codebases intentionally use EF Core in Application query handlers. If a strict rule creates too many findings, do not delete the rule immediately. Prefer one of these options:

1. Change severity from `error` to `warning` while the team migrates gradually.
2. Add `max_findings_per_project` to show only the first few examples.
3. Add `exclude` patterns for generated code or legacy folders.
4. Narrow the pattern from a namespace to a more specific concrete type.

Example:

```json
{
  "layer": "application",
  "pattern": "Microsoft.EntityFrameworkCore",
  "severity": "warning",
  "max_findings_per_project": 5,
  "exclude": ["**/Generated/**", "**/*.g.cs"],
  "message": "Application currently uses EF Core. Prefer abstractions or move data access to Infrastructure over time."
}
```

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
