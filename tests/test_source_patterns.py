from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contextguard.config import ContextGuardConfig, SourcePatternRule, load_config
from contextguard.scanners.dotnet import scan_dotnet


class SourcePatternTests(unittest.TestCase):
    def test_detects_forbidden_source_pattern_in_application_layer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app = root / "src" / "Sample.Application"
            app.mkdir(parents=True)

            (app / "Sample.Application.csproj").write_text(
                """
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
""".strip(),
                encoding="utf-8",
            )
            (app / "BadHandler.cs").write_text(
                "using Microsoft.EntityFrameworkCore;\npublic class BadHandler {}",
                encoding="utf-8",
            )

            config = ContextGuardConfig(
                layer_patterns={"application": ["application"]},
                forbidden_dependencies={},
                forbidden_source_patterns=[
                    SourcePatternRule(
                        layer="application",
                        pattern="Microsoft.EntityFrameworkCore",
                        message="Application projects must not use EF Core.",
                    )
                ],
            )
            result = scan_dotnet(root, config=config)

            self.assertEqual(result.error_count, 1)
            self.assertEqual(result.violations[0].rule_id, "forbidden-source-pattern")
            self.assertIn("BadHandler.cs:1", result.violations[0].message)

    def test_source_pattern_warning_does_not_fail_validation_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            api = root / "src" / "Sample.WebApi"
            api.mkdir(parents=True)

            (api / "Sample.WebApi.csproj").write_text(
                """
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
""".strip(),
                encoding="utf-8",
            )
            (api / "Controller.cs").write_text(
                "public class Controller { private object DbContext; }",
                encoding="utf-8",
            )

            config = ContextGuardConfig(
                layer_patterns={"webapi": ["webapi"]},
                forbidden_dependencies={},
                forbidden_source_patterns=[
                    SourcePatternRule(
                        layer="webapi",
                        pattern="DbContext",
                        message="WebApi should avoid direct DbContext usage.",
                        severity="warning",
                    )
                ],
            )
            result = scan_dotnet(root, config=config)

            self.assertEqual(result.error_count, 0)
            self.assertEqual(result.warning_count, 1)

    def test_source_pattern_exclude_skips_matching_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app = root / "src" / "Sample.Application"
            generated = app / "Generated"
            generated.mkdir(parents=True)

            (app / "Sample.Application.csproj").write_text(
                """
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
""".strip(),
                encoding="utf-8",
            )
            (generated / "GeneratedHandler.cs").write_text(
                "using Microsoft.EntityFrameworkCore;",
                encoding="utf-8",
            )

            config = ContextGuardConfig(
                layer_patterns={"application": ["application"]},
                forbidden_dependencies={},
                forbidden_source_patterns=[
                    SourcePatternRule(
                        layer="application",
                        pattern="Microsoft.EntityFrameworkCore",
                        message="Application projects must not use EF Core.",
                        exclude=["**/Generated/**"],
                    )
                ],
            )
            result = scan_dotnet(root, config=config)

            self.assertEqual(result.error_count, 0)

    def test_source_pattern_max_findings_limits_noise(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app = root / "src" / "Sample.Application"
            app.mkdir(parents=True)

            (app / "Sample.Application.csproj").write_text(
                """
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
""".strip(),
                encoding="utf-8",
            )
            for index in range(3):
                (app / f"Bad{index}.cs").write_text("using Microsoft.EntityFrameworkCore;", encoding="utf-8")

            config = ContextGuardConfig(
                layer_patterns={"application": ["application"]},
                forbidden_dependencies={},
                forbidden_source_patterns=[
                    SourcePatternRule(
                        layer="application",
                        pattern="Microsoft.EntityFrameworkCore",
                        message="Application projects must not use EF Core.",
                        max_findings_per_project=2,
                    )
                ],
            )
            result = scan_dotnet(root, config=config)

            self.assertEqual(result.error_count, 2)

    def test_source_pattern_regex_match_type(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app = root / "src" / "Sample.Application"
            app.mkdir(parents=True)

            (app / "Sample.Application.csproj").write_text(
                """
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
""".strip(),
                encoding="utf-8",
            )
            (app / "BadHandler.cs").write_text("using Grpc.Client;", encoding="utf-8")

            config = ContextGuardConfig(
                layer_patterns={"application": ["application"]},
                forbidden_dependencies={},
                forbidden_source_patterns=[
                    SourcePatternRule(
                        layer="application",
                        pattern=r"using\s+Grpc\.Client",
                        message="Application must not use concrete gRPC clients.",
                        match_type="regex",
                    )
                ],
            )
            result = scan_dotnet(root, config=config)

            self.assertEqual(result.error_count, 1)

    def test_loads_source_pattern_rules_from_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_dir = root / ".contextguard"
            config_dir.mkdir()
            (config_dir / "config.json").write_text(
                """
{
  "forbidden_source_patterns": [
    {
      "layer": "application",
      "pattern": "Grpc.Client",
      "message": "Application must not use concrete gRPC clients.",
      "severity": "error",
      "include": ["**/*.cs"],
      "exclude": ["**/Generated/**"],
      "max_findings_per_project": 3
    }
  ]
}
""".strip(),
                encoding="utf-8",
            )

            config = load_config(root)

            self.assertEqual(len(config.forbidden_source_patterns), 1)
            self.assertEqual(config.forbidden_source_patterns[0].pattern, "Grpc.Client")
            self.assertEqual(config.forbidden_source_patterns[0].exclude, ["**/Generated/**"])
            self.assertEqual(config.forbidden_source_patterns[0].max_findings_per_project, 3)


if __name__ == "__main__":
    unittest.main()
