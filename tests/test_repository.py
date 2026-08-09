import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
THEME_ROOT = REPOSITORY_ROOT / "themes" / "hugo-bearneo"


class RepositoryTests(unittest.TestCase):
    def test_vendored_theme_records_license_and_upstream_provenance(self):
        license_file = THEME_ROOT / "LICENSE"
        self.assertTrue(license_file.is_file())
        self.assertIn("MIT License", license_file.read_text(encoding="utf-8"))

        upstream = THEME_ROOT / "UPSTREAM.md"
        self.assertTrue(upstream.is_file())
        provenance = upstream.read_text(encoding="utf-8")
        self.assertIn("https://github.com/rokcso/hugo-bearneo", provenance)
        self.assertIn("f5c57c5ea39a091f0167af6312f4d4e385df2e6c", provenance)

    def test_vendored_theme_does_not_contain_nested_git_metadata(self):
        nested_git_paths = list(THEME_ROOT.rglob(".git"))
        self.assertEqual([], nested_git_paths)

    def test_static_nojekyll_marker_exists(self):
        self.assertTrue((REPOSITORY_ROOT / "static" / ".nojekyll").is_file())


if __name__ == "__main__":
    unittest.main()
