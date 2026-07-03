from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contextguard.scanners.dotnet import infer_layer, scan_dotnet


class DotnetScannerTests(unittest.TestCase):
    def test_infers_common_clean_architecture_layers(self) -> None:
        self.assertEqual(infer_layer("Sample.Domain", Path("src/Sample.Domain/Sample.Domain.csproj")), "domain")
        self.assertEqual(infer_layer("Sample.Application", Path("src/Sample.Application/Sample.Application.csproj")), "application")
        self.assertEqual(infer_layer("Sample.Infrastructure", Path("src/Sample.Infrastructure/Sample.Infrastructure.csproj")), "infrastructure")
        self.assertEqual(infer_layer("Sample.WebApi", Path("src/Sample.WebApi/Sample.WebApi.csproj")), "webapi")
        self.assertEqual(infer_layer("Sample.Tests", Path("tests/Sample.Tests/Sample.Tests.csproj")), "tests")

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


if __name__ == "__main__":
    unittest.main()
