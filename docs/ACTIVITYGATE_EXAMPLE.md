# ActivityGate example finding

This document captures the first real ContextGuard finding tested against the ActivityGate codebase.

## Command

```powershell
python -m contextguard analyze . --show-deps
```

## Detected finding

```text
[error] ActivityGate.Application (application) must not reference Grpc.Client (client).
```

## Why this matters

In a Clean Architecture style codebase, the Application layer should not depend directly on external client implementations.

If `Grpc.Client` contains generated clients, communication wrappers, channels, service clients, or integration logic, then the dependency should move outward.

A better direction is:

```text
ActivityGate.Application
  -> defines an interface or abstraction

ActivityGate.Infrastructure
  -> references Grpc.Client
  -> implements the Application abstraction

ActivityGate.Api / ActivityGate.WebApi
  -> wires the implementation through dependency injection
```

## When it is not an error

If `Grpc.Client` contains only shared contracts, request/response DTOs, or proto-generated message types with no external communication implementation, the project may be better classified as `contract` instead of `client`.

In that case, the repository config can map it like this:

```json
{
  "layer_patterns": {
    "contract": ["grpc.client"]
  },
  "forbidden_dependencies": {
    "application": ["infrastructure", "webapi", "tests", "subscriber"]
  }
}
```

## Product lesson for ContextGuard

A useful architecture tool should not only say that a rule was violated. It should explain:

- Why the dependency is risky.
- How to fix the code if the rule is correct.
- How to adjust config if the dependency is intentional.

This is why ContextGuard now has:

```powershell
python -m contextguard explain .
```
