import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_goal_and_outputs_are_ignored(self):
        text = (ROOT / ".gitignore").read_text()
        self.assertIn("goal.md", text)
        self.assertIn("build/", text)

    def test_ci_separates_read_only_validation_and_attestation(self):
        text = (ROOT / ".github/workflows/ci.yml").read_text()
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("id-token: write", text)
        self.assertIn("attest-build-provenance@v2", text)


if __name__ == "__main__":
    unittest.main()
