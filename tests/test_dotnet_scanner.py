from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contextguard.config import ContextGuardConfig, load_config
from contextguard.scanners.dotnet import infer_layer, scan_dotnet


class DotnetScannerTests(unittest.TestCase):
    def test_infers_common_clean_architecture_layers(self) -> None:
        self.assertEqual(infer_layer("Sample.Domain", Path("src/Sample.Domain/Sample.Domain.csproj")), "domain")
        self.assertEqual(infer_layer("Sample.Application", Path("src/Sample.Application/Sample.Application.csproj")), "application")
        self.assertEqual(infer_layer("Sample.Infrastructure", Path("src/Sample.Infrastructure/Sample.Infrastructure.csproj")), "infrastructure")
        self.assertEqual(infer_layer("Sample.WebApi", Path("src/Sample.WebApi/Sample.WebApi.csproj")), "webapi")
        self.assertEqual(infer_layer("Sample.Tests", Path("tests/Sample.Tests/Sample.Tests.csproj")), "tests")

    def test_infers_custom_layer_patterns_from_config(self) -> None:
        config = ContextGuardConfig(
            layer_patterns={"core": ["core"], "adapter": ["adapter"]},
            forbidden_dependencies={"core": ["adapter"]},
        )

        self.assertEqual(infer_layer("Sample.Core", Path("src/Sample.Core/Sample.Core.csproj"), config), "core")
        self.assertEqual(infer_layer("Sample.Adapter", Path("src/Sample.Adapter/Sample.Adapter.csproj"), config), "adapter")

    def test_loads_contextguard_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_dir = root / ".contextguard"
            config_dir.mkdir()
            (config_dir / "config.json").write_text(
                """
{
  "layer_patterns": {
    "core": ["core"],
    "adapter": ["adapter"]
  },
  "forbidden_dependencies": {
    "core": ["adapter"]
  }
}
""".strip(),
                encoding="utf-8",
            )

            config = load_config(root)

            self.assertEqual(config.layer_patterns["core"], ["core"])
            self.assertEqual(config.forbidden_dependencies["core"], ["adapter"])

    def test_detects_invalid_application_to_infrastructure_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            application = root / "src" / "Sample.Application"
            infrastructure = root / "src" / "Sample.Infrastructure"
            application.mkdir(parents=True)
            infrastructure.mkdir(parents=True)

            (root / "Sample.sln").write_text(
                '\n'.join(
                    [
                        'Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "Sample.Application", "src\\Sample.Application\\Sample.Application.csproj", "{11111111-1111-1111-1111-111111111111}"',
                        'EndProject',
                        'Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "Sample.Infrastructure", "src\\Sample.Infrastructure\\Sample.Infrastructure.csproj", "{22222222-2222-2222-2222-222222222222}"',
                        'EndProject',
                    ]
                ),
                encoding="utf-8",
            )

            (application / "Sample.Application.csproj").write_text(
                """
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <ProjectReference Include="..\\Sample.Infrastructure\\Sample.Infrastructure.csproj" />
  </ItemGroup>
</Project>
""".strip(),
                encoding="utf-8",
            )
            (infrastructure / "Sample.Infrastructure.csproj").write_text(
                """
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
""".strip(),
                encoding="utf-8",
            )

            result = scan_dotnet(root)

            self.assertEqual(len(result.projects), 2)
            self.assertEqual(len(result.violations), 1)
            self.assertIn("must not reference", result.violations[0].message)

    def test_detects_invalid_custom_dependency_rule(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            core = root / "src" / "Sample.Core"
            adapter = root / "src" / "Sample.Adapter"
            core.mkdir(parents=True)
            adapter.mkdir(parents=True)

            (core / "Sample.Core.csproj").write_text(
                """
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <ProjectReference Include="..\\Sample.Adapter\\Sample.Adapter.csproj" />
  </ItemGroup>
</Project>
""".strip(),
                encoding="utf-8",
            )
            (adapter / "Sample.Adapter.csproj").write_text(
                """
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
""".strip(),
                encoding="utf-8",
            )

            config = ContextGuardConfig(
                layer_patterns={"core": ["core"], "adapter": ["adapter"]},
                forbidden_dependencies={"core": ["adapter"]},
            )
            result = scan_dotnet(root, config=config)

            self.assertEqual(len(result.projects), 2)
            self.assertEqual(len(result.violations), 1)
            self.assertEqual(result.violations[0].rule_id, "layer-dependency")


if __name__ == "__main__":
    unittest.main()
