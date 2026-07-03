from __future__ import annotations

from contextguard.models import ViolationInfo


RULE_EXPLANATIONS: dict[str, dict[str, str]] = {
    "layer-dependency": {
        "title": "Invalid layer dependency",
        "why": (
            "A project depends on another project from a layer that should stay outside of its boundary. "
            "This can make inner layers depend on infrastructure, delivery mechanisms, or external clients."
        ),
        "fix": (
            "Move the implementation detail to an outer layer, usually Infrastructure. "
            "Keep an interface or abstraction in the inner layer and register the implementation through dependency injection."
        ),
        "config": (
            "If the dependency is intentional, update `.contextguard/config.json` and remove the target layer "
            "from the source layer's `forbidden_dependencies` list."
        ),
    },
    "unknown-project-layer": {
        "title": "Unknown project layer",
        "why": (
            "ContextGuard could not map this project to a known architecture layer. "
            "Rules may not be applied correctly until the layer is known."
        ),
        "fix": (
            "Add a pattern for this project in `.contextguard/config.json` under `layer_patterns`. "
            "For example, map worker projects to `worker`, subscribers to `subscriber`, or shared contracts to `contract`."
        ),
        "config": (
            "After adding the new layer pattern, also define its dependency rules under `forbidden_dependencies`."
        ),
    },
}


def explain_rule(rule_id: str) -> str:
    explanation = RULE_EXPLANATIONS.get(rule_id)
    if explanation is None:
        known_rules = ", ".join(sorted(RULE_EXPLANATIONS))
        return f"No explanation is registered for rule `{rule_id}`. Known rules: {known_rules}."

    return _format_rule(rule_id, explanation)


def explain_violation(violation: ViolationInfo) -> str:
    explanation = RULE_EXPLANATIONS.get(violation.rule_id)
    if explanation is None:
        return f"[{violation.severity}] {violation.rule_id}: {violation.message}"

    lines = [
        f"[{violation.severity}] {explanation['title']}",
        f"Finding: {violation.message}",
        "",
        f"Why it matters: {explanation['why']}",
        f"Recommended fix: {explanation['fix']}",
        f"If intentional: {explanation['config']}",
    ]
    return "\n".join(lines)


def _format_rule(rule_id: str, explanation: dict[str, str]) -> str:
    lines = [
        f"Rule: {rule_id}",
        f"Title: {explanation['title']}",
        "",
        f"Why it matters: {explanation['why']}",
        f"Recommended fix: {explanation['fix']}",
        f"If intentional: {explanation['config']}",
    ]
    return "\n".join(lines)
