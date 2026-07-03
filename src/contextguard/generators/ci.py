from __future__ import annotations

from pathlib import Path

GITHUB_ACTIONS_WORKFLOW = '''name: ContextGuard

on:
  push:
    branches: [main]

jobs:
  architecture:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install ContextGuard
        run: python -m pip install git+https://github.com/smael-aftersearch/contextguard.git

      - name: Validate architecture rules
        run: python -m contextguard validate .
'''


def generate_github_actions_workflow(root: Path, force: bool = False) -> Path:
    root = root.resolve()
    workflow_path = root / ".github" / "workflows" / "contextguard.yml"

    if workflow_path.exists() and not force:
        raise ValueError(f"Workflow already exists: {workflow_path}. Use --force to overwrite it.")

    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(GITHUB_ACTIONS_WORKFLOW, encoding="utf-8")
    return workflow_path
