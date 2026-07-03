from __future__ import annotations

import unittest

from contextguard.explain import explain_rule, explain_violation
from contextguard.models import ViolationInfo


class ExplainTests(unittest.TestCase):
    def test_explains_known_rule(self) -> None:
        text = explain_rule("layer-dependency")

        self.assertIn("Invalid layer dependency", text)
        self.assertIn("Recommended fix", text)

    def test_explains_unknown_rule(self) -> None:
        text = explain_rule("not-a-real-rule")

        self.assertIn("No explanation is registered", text)
        self.assertIn("layer-dependency", text)

    def test_explains_violation_with_guidance(self) -> None:
        violation = ViolationInfo(
            rule_id="layer-dependency",
            source="ActivityGate.Application",
            target="Grpc.Client",
            message="ActivityGate.Application must not reference Grpc.Client.",
        )

        text = explain_violation(violation)

        self.assertIn("ActivityGate.Application", text)
        self.assertIn("Why it matters", text)
        self.assertIn("Recommended fix", text)


if __name__ == "__main__":
    unittest.main()
