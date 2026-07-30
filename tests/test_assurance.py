import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from assurance import (  # noqa: E402
    AssuranceError,
    apply_exceptions,
    load_json,
    normalize_changed,
    scan_file,
    validate_catalog,
    validate_exceptions,
)


class AssuranceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_json(ROOT / "config/control-catalog.json")
        cls.rules = validate_catalog(cls.catalog)

    def test_compliant_fixtures_have_no_findings(self):
        for relative in ("examples/compliant/main.bicep", "examples/compliant/main.tf"):
            with self.subTest(relative=relative):
                self.assertEqual(scan_file(ROOT / relative, relative, self.rules), [])

    def test_noncompliant_fixtures_find_all_material_classes(self):
        findings = []
        for relative in (
            "examples/noncompliant/main.bicep",
            "examples/noncompliant/main.tf",
        ):
            findings.extend(scan_file(ROOT / relative, relative, self.rules))
        self.assertEqual(
            {finding["rule_id"] for finding in findings},
            {"AZ-NET-001", "AZ-CRYPTO-001", "AZ-IDENTITY-001", "AZ-DATA-001"},
        )
        self.assertTrue(all(finding["line"] > 0 for finding in findings))

    def test_exception_is_exact_and_auditable(self):
        findings = scan_file(
            ROOT / "examples/noncompliant/main.bicep",
            "examples/noncompliant/main.bicep",
            self.rules,
        )
        exception = {
            "id": "EX-42",
            "rule_id": "AZ-NET-001",
            "path": "examples/noncompliant/main.bicep",
        }
        apply_exceptions(findings, [exception])
        suppressed = [item for item in findings if item["suppressed"]]
        self.assertEqual(len(suppressed), 1)
        self.assertEqual(suppressed[0]["exception_id"], "EX-42")

    def test_expired_exception_is_rejected(self):
        document = {
            "exceptions": [
                {
                    "id": "EX-1",
                    "rule_id": "AZ-NET-001",
                    "path": "main.tf",
                    "owner": "security",
                    "justification": "Temporary migration window",
                    "expires_at": "2020-01-01T00:00:00Z",
                }
            ]
        }
        with self.assertRaisesRegex(AssuranceError, "expired"):
            validate_exceptions(
                document,
                {"AZ-NET-001"},
                dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
            )

    def test_changed_files_are_sorted_deduplicated_and_bounded(self):
        values = normalize_changed(
            [
                "examples/compliant/main.tf\n",
                "../outside.tf\n",
                "/tmp/absolute.bicep\n",
                "README.md\n",
                "examples/compliant/main.tf\n",
                "examples/compliant/main.bicep\n",
            ],
            ROOT,
        )
        self.assertEqual(
            values,
            ["examples/compliant/main.bicep", "examples/compliant/main.tf"],
        )

    def test_cli_fails_closed_and_writes_sarif(self):
        with tempfile.TemporaryDirectory() as output:
            result = subprocess.run(
                [
                    sys.executable,
                    "src/assurance.py",
                    "scan",
                    "examples/noncompliant/main.bicep",
                    "--catalog",
                    "config/control-catalog.json",
                    "--exceptions",
                    "config/exceptions.json",
                    "--output",
                    output,
                    "--fail-on",
                    "high",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            report = json.loads((Path(output) / "report.json").read_text())
            sarif = json.loads((Path(output) / "results.sarif").read_text())
            manifest = json.loads((Path(output) / "manifest.json").read_text())
            self.assertEqual(report["summary"]["gate"], "fail")
            self.assertEqual(sarif["version"], "2.1.0")
            self.assertIn("report.json", manifest["artifacts"])


if __name__ == "__main__":
    unittest.main()
