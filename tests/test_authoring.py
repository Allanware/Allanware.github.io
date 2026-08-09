from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.validate_interaction_ids import read_front_matter


ROOT = Path(__file__).resolve().parents[1]
SITE_DIRECTORIES = [
    "archetypes",
    "assets",
    "i18n",
    "layouts",
    "scripts",
    "static",
    "themes",
]


def body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    closing = text.find("\n+++\n", 4)
    if closing == -1:
        raise AssertionError(f"missing closing front-matter delimiter in {path}")
    return text[closing + 5 :]


class AuthoringWorkflowTests(unittest.TestCase):
    def test_documented_commands_create_safe_standalone_and_paired_bundles(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            site = temporary_root / "site"
            site.mkdir()
            (site / "content").mkdir()
            shutil.copy2(ROOT / "hugo.toml", site / "hugo.toml")
            for directory in SITE_DIRECTORIES:
                shutil.copytree(ROOT / directory, site / directory)

            commands = [
                [
                    "hugo",
                    "new",
                    "content",
                    "--kind",
                    "blog",
                    "content/blog/my-post/index.en.md",
                ],
                ["python3", "scripts/new_translation.py", "my-post", "en", "zh"],
                [
                    "hugo",
                    "new",
                    "content",
                    "--kind",
                    "blog",
                    "content/blog/chinese-only/index.zh.md",
                ],
            ]
            for command in commands:
                subprocess.run(
                    command,
                    cwd=site,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            english_path = site / "content/blog/my-post/index.en.md"
            chinese_path = site / "content/blog/my-post/index.zh.md"
            chinese_only_path = site / "content/blog/chinese-only/index.zh.md"
            english = read_front_matter(english_path)
            chinese = read_front_matter(chinese_path)
            chinese_only = read_front_matter(chinese_only_path)

            self.assertEqual("My Post", english["title"])
            self.assertEqual("my-post", english["interactionId"])
            self.assertEqual(english, chinese)
            self.assertEqual(english_path.read_bytes(), chinese_path.read_bytes())
            self.assertEqual("chinese-only", chinese_only["interactionId"])
            self.assertEqual("Chinese Only", chinese_only["title"])
            for front_matter in [english, chinese, chinese_only]:
                self.assertTrue(front_matter["draft"])
                self.assertEqual([], front_matter["tags"])
                self.assertRegex(
                    front_matter["date"],
                    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
                )
                self.assertEqual(front_matter["date"], front_matter["lastmod"])
            self.assertEqual("\n## Introduction\n", body(english_path))
            self.assertEqual("\n## Introduction\n", body(chinese_only_path))

            sentinel = chinese_path.read_bytes() + "\n中文译文。\n".encode("utf-8")
            chinese_path.write_bytes(sentinel)
            refusal = subprocess.run(
                ["python3", "scripts/new_translation.py", "my-post", "en", "zh"],
                cwd=site,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, refusal.returncode)
            self.assertIn("already exists", refusal.stderr)
            self.assertEqual(sentinel, chinese_path.read_bytes())

            public = temporary_root / "public"
            subprocess.run(
                [
                    "hugo",
                    "--source",
                    str(site),
                    "--destination",
                    str(public),
                    "--baseURL",
                    "https://example.test/",
                    "--buildDrafts",
                    "--cleanDestinationDir",
                    "--noBuildLock",
                    "--panicOnWarning",
                    "--cacheDir",
                    str(temporary_root / "cache"),
                ],
                cwd=site,
                check=True,
                capture_output=True,
                text=True,
            )
            english_html = (public / "p/my-post/index.html").read_text(encoding="utf-8")
            chinese_html = (public / "zh/p/my-post/index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn('href="/zh/p/my-post/"', english_html)
            self.assertIn('href="/p/my-post/"', chinese_html)
            self.assertTrue((public / "zh/p/chinese-only/index.html").is_file())
            self.assertFalse((public / "p/chinese-only/index.html").exists())


if __name__ == "__main__":
    unittest.main()
