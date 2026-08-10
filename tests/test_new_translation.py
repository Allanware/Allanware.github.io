from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import unittest

from scripts.new_translation import create_translation


ROOT = Path(__file__).resolve().parents[1]


class TranslationCopyTests(unittest.TestCase):
    def make_source(self, content: Path, *, section: str = "blog") -> Path:
        source = content / section / "my-post/index.en.md"
        source.parent.mkdir(parents=True)
        source.write_bytes(
            '+++\ninteractionId = "my-post"\n+++\n\nBody 中文\n'.encode("utf-8")
        )
        return source

    def test_copies_source_verbatim_to_new_language_file(self):
        with TemporaryDirectory() as temporary:
            content = Path(temporary)
            source = self.make_source(content)

            target = create_translation(content, "my-post", "en", "zh")

            self.assertEqual(content / "blog/my-post/index.zh.md", target)
            self.assertEqual(source.read_bytes(), target.read_bytes())

    def test_copies_a_project_translation_verbatim(self):
        with TemporaryDirectory() as temporary:
            content = Path(temporary)
            source = self.make_source(content, section="projects")

            target = create_translation(
                content,
                "my-post",
                "en",
                "zh",
                section="projects",
            )

            self.assertEqual(content / "projects/my-post/index.zh.md", target)
            self.assertEqual(source.read_bytes(), target.read_bytes())

    def test_cli_copies_a_project_translation(self):
        with TemporaryDirectory() as temporary:
            content = Path(temporary) / "content"
            source = self.make_source(content, section="projects")
            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts/new_translation.py"),
                    "my-post",
                    "en",
                    "zh",
                    "--section",
                    "projects",
                    "--content-root",
                    str(content),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            target = content / "projects/my-post/index.zh.md"
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(f"Created {target}", result.stdout)
            self.assertEqual(source.read_bytes(), target.read_bytes())

    def test_refuses_to_overwrite_and_preserves_existing_target_bytes(self):
        with TemporaryDirectory() as temporary:
            content = Path(temporary)
            self.make_source(content)
            target = content / "blog/my-post/index.zh.md"
            sentinel = b"existing translation must remain byte-identical\n"
            target.write_bytes(sentinel)

            with self.assertRaisesRegex(FileExistsError, "already exists"):
                create_translation(content, "my-post", "en", "zh")

            self.assertEqual(sentinel, target.read_bytes())

    def test_rejects_a_missing_source(self):
        with TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                FileNotFoundError, "source translation does not exist"
            ):
                create_translation(Path(temporary), "missing", "en", "zh")

    def test_rejects_slugs_that_could_escape_or_alias_the_bundle(self):
        invalid_slugs = [
            "../escape",
            "nested/escape",
            ".",
            "my_post",
            "My-Post",
            "-leading",
            "trailing-",
            "double--hyphen",
        ]
        with TemporaryDirectory() as temporary:
            content = Path(temporary)
            self.make_source(content)
            for slug in invalid_slugs:
                with self.subTest(slug=slug):
                    with self.assertRaisesRegex(ValueError, "slug must"):
                        create_translation(content, slug, "en", "zh")

    def test_rejects_unknown_or_same_languages(self):
        with TemporaryDirectory() as temporary:
            content = Path(temporary)
            self.make_source(content)
            for source_language, target_language in [
                ("fr", "zh"),
                ("en", "de"),
                ("EN", "zh"),
            ]:
                with self.subTest(
                    source_language=source_language,
                    target_language=target_language,
                ):
                    with self.assertRaisesRegex(ValueError, "languages must be en or zh"):
                        create_translation(
                            content,
                            "my-post",
                            source_language,
                            target_language,
                        )

            with self.assertRaisesRegex(ValueError, "must differ"):
                create_translation(content, "my-post", "en", "en")

    def test_rejects_an_unknown_section(self):
        with TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                ValueError,
                "section must be blog or projects",
            ):
                create_translation(
                    Path(temporary),
                    "my-post",
                    "en",
                    "zh",
                    section="pages",
                )

    def test_rejects_a_blog_root_symlink_that_escapes_content(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            outside = temporary_root / "outside"
            source = outside / "my-post/index.en.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                '+++\ninteractionId = "my-post"\n+++\n\nOutside\n',
                encoding="utf-8",
            )
            content.mkdir()
            (content / "blog").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "blog content root"):
                create_translation(content, "my-post", "en", "zh")

            self.assertFalse((outside / "my-post/index.zh.md").exists())


if __name__ == "__main__":
    unittest.main()
