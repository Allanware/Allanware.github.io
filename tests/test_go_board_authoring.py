from collections import Counter
from html import unescape
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import urlsplit

from scripts.check_site import check_site
from scripts.validate_interaction_ids import read_front_matter


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
HAN_PATTERN = re.compile(r"[一-鿿]")
SHORTCODE_PATTERN = re.compile(r"{{<\s*go-board\s+(?P<params>.*?)\s*>}}", re.DOTALL)
ATTRIBUTE_PATTERN = re.compile(r'([a-zA-Z][\w-]*)="([^"]*)"')
RENDERED_GO_BOARD_FIGURE_PATTERN = re.compile(
    r'(?P<opening><figure\b(?=[^>]*\sdata-go-board(?:\s|=|>))[^>]*>)'
    r'(?P<contents>.*?</figure\s*>)',
    re.DOTALL,
)
FIGCAPTION_PATTERN = re.compile(
    r"<figcaption\b[^>]*>(?P<caption>.*?)</figcaption\s*>",
    re.DOTALL,
)


def go_board_shortcodes(text: str) -> list[dict[str, str]]:
    return [
        dict(ATTRIBUTE_PATTERN.findall(match.group("params")))
        for match in SHORTCODE_PATTERN.finditer(text)
    ]


def board_pages() -> list[Path]:
    """Every published page that embeds at least one Go board."""
    return sorted(
        path
        for path in CONTENT.rglob("index.*.md")
        if SHORTCODE_PATTERN.search(path.read_text(encoding="utf-8"))
    )


def selector_of(attributes: dict[str, str]) -> tuple[str, str]:
    """The (kind, value) pair the shortcode selects, including the default."""
    for kind in ("move", "path"):
        if kind in attributes:
            return kind, attributes[kind]
    return "move", "0"


def board_specification(attributes: dict[str, str]) -> tuple[str, str, str, str]:
    kind, value = selector_of(attributes)
    return attributes.get("src", ""), kind, value, attributes.get("caption", "")


def assert_valid_local_board(
    test_case: unittest.TestCase,
    attributes: dict[str, str],
    bundle: Path,
) -> None:
    test_case.assertTrue(attributes.get("caption", "").strip())
    source = Path(attributes.get("src", ""))
    test_case.assertEqual(".sgf", source.suffix.lower())
    test_case.assertFalse(source.is_absolute())
    test_case.assertNotIn("..", source.parts)
    test_case.assertTrue((bundle / source).is_file())

    selectors = set(attributes) & {"move", "path"}
    test_case.assertLessEqual(len(selectors), 1)
    if "move" in selectors:
        test_case.assertRegex(attributes["move"], r"^[0-9]+$")
    elif "path" in selectors:
        test_case.assertRegex(attributes["path"], r"^(?:N[0-9]+|B[1-9][0-9]*)+$")


class PublishedGoBoardContentTests(unittest.TestCase):
    """Lint every authored Go board instead of pinning one post's bytes.

    These assertions describe what any Go-board post must satisfy, so editing,
    renaming, or re-exporting a record keeps them meaningful.
    """

    def setUp(self):
        self.pages = board_pages()
        if not self.pages:
            self.skipTest("no published content embeds a Go board")

    def test_every_authored_board_names_a_valid_local_record(self):
        for page in self.pages:
            boards = go_board_shortcodes(page.read_text(encoding="utf-8"))
            self.assertTrue(boards)
            for board in boards:
                with self.subTest(page=page.relative_to(ROOT), board=board):
                    assert_valid_local_board(self, board, page.parent)

    def test_referenced_records_are_non_empty_sgf_collections(self):
        for page in self.pages:
            for board in go_board_shortcodes(page.read_text(encoding="utf-8")):
                record = page.parent / board["src"]
                with self.subTest(record=record.relative_to(ROOT)):
                    payload = record.read_text(encoding="utf-8").lstrip("﻿")
                    self.assertRegex(payload.lstrip(), r"^\(\s*;")
                    self.assertIn("FF[", payload)

    def test_translations_share_identity_and_mirror_their_board_selectors(self):
        bundles: dict[Path, list[Path]] = {}
        for page in self.pages:
            bundles.setdefault(page.parent, []).append(page)

        for bundle, pages in bundles.items():
            if len(pages) < 2:
                continue
            with self.subTest(bundle=bundle.relative_to(ROOT)):
                front_matter = {
                    page: read_front_matter(page) for page in pages
                }
                identities = {
                    matter.get("interactionId") for matter in front_matter.values()
                }
                self.assertEqual(1, len(identities), identities)
                self.assertEqual(
                    1,
                    len({matter.get("draft") for matter in front_matter.values()}),
                )

                selectors = {
                    page: [
                        (board.get("src"), *selector_of(board))
                        for board in go_board_shortcodes(
                            page.read_text(encoding="utf-8")
                        )
                    ]
                    for page in pages
                }
                reference = selectors[pages[0]]
                for page, authored in selectors.items():
                    self.assertEqual(reference, authored, page.relative_to(ROOT))

    def test_chinese_pages_translate_their_titles_and_captions(self):
        for page in self.pages:
            if not page.name.endswith(".zh.md"):
                continue
            english = page.with_name(page.name.replace(".zh.md", ".en.md"))
            with self.subTest(page=page.relative_to(ROOT)):
                self.assertRegex(
                    str(read_front_matter(page).get("title", "")),
                    HAN_PATTERN,
                )
                chinese_captions = [
                    board.get("caption", "")
                    for board in go_board_shortcodes(
                        page.read_text(encoding="utf-8")
                    )
                ]
                for caption in chinese_captions:
                    self.assertRegex(caption, HAN_PATTERN)
                if not english.is_file():
                    continue
                english_captions = [
                    board.get("caption", "")
                    for board in go_board_shortcodes(
                        english.read_text(encoding="utf-8")
                    )
                ]
                self.assertEqual(len(english_captions), len(chinese_captions))
                for chinese, source in zip(chinese_captions, english_captions):
                    self.assertNotEqual(source, chinese)


class RenderedGoBoardTests(unittest.TestCase):
    def test_published_pages_render_every_authored_board(self):
        pages = board_pages()
        if not pages:
            self.skipTest("no published content embeds a Go board")

        authored = Counter()
        records: dict[str, set[bytes]] = {}
        for page in pages:
            for board in go_board_shortcodes(page.read_text(encoding="utf-8")):
                authored[board_specification(board)] += 1
                records.setdefault(board["src"], set()).add(
                    (page.parent / board["src"]).read_bytes()
                )
        self.assertTrue(authored)

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            public = temporary_root / "public"
            base_url = "https://example.test/project/"
            subprocess.run(
                [
                    "hugo",
                    "--source", str(ROOT),
                    "--destination", str(public),
                    "--baseURL", base_url,
                    "--buildDrafts",
                    "--cleanDestinationDir",
                    "--panicOnWarning",
                    "--noBuildLock",
                    "--cacheDir", str(temporary_root / "cache"),
                    "--environment", "production",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual([], check_site(public, base_url))
            base_path = urlsplit(base_url).path.rstrip("/")

            rendered = Counter()
            sgf_urls: set[str] = set()
            for document in sorted(public.rglob("*.html")):
                html = document.read_text(encoding="utf-8")
                figures = list(RENDERED_GO_BOARD_FIGURE_PATTERN.finditer(html))
                if not figures:
                    continue
                identifiers = []
                for figure in figures:
                    attributes = dict(
                        ATTRIBUTE_PATTERN.findall(figure.group("opening"))
                    )
                    with self.subTest(page=document.relative_to(public)):
                        identifier = attributes.get("id")
                        self.assertIsNotNone(identifier)
                        self.assertRegex(identifier, r"^go-board-[0-9a-f]{12}$")
                        identifiers.append(identifier)

                        sgf_url = attributes.get("data-sgf-url")
                        self.assertIsNotNone(sgf_url)
                        self.assertTrue(sgf_url.startswith(f"{base_path}/"), sgf_url)
                        sgf_urls.add(sgf_url)

                        captions = [
                            unescape(caption)
                            for caption in FIGCAPTION_PATTERN.findall(
                                figure.group(0)
                            )
                        ]
                        self.assertEqual(1, len(captions))
                        rendered[(
                            sgf_url.rsplit("/", 1)[-1],
                            attributes.get("data-selector-kind"),
                            attributes.get("data-selector-value"),
                            captions[0],
                        )] += 1
                with self.subTest(page=document.relative_to(public)):
                    self.assertEqual(len(identifiers), len(set(identifiers)))

            self.assertEqual(authored, rendered)

            for sgf_url in sorted(sgf_urls):
                published = public / sgf_url.removeprefix(base_path).lstrip("/")
                name = sgf_url.rsplit("/", 1)[-1]
                with self.subTest(sgf_url=sgf_url):
                    self.assertTrue(published.is_file(), published)
                    self.assertIn(published.read_bytes(), records[name])


class GoBoardAuthoringDocumentationTests(unittest.TestCase):
    def readme_section(self) -> str:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        match = re.search(
            r"^## Interactive Go boards\n(?P<body>.*?)(?=^## |\Z)",
            readme,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match)
        return match.group("body")

    def test_readme_documents_a_resolvable_exact_path_example(self):
        examples = go_board_shortcodes(self.readme_section())
        self.assertTrue(examples, "document at least one shortcode example")

        advanced = next(
            (example for example in examples if "path" in example),
            None,
        )
        self.assertIsNotNone(advanced, "document an exact-path shortcode example")
        self.assertTrue(advanced.get("path"))
        self.assertRegex(advanced["path"], r"^(?:N[0-9]+|B[1-9][0-9]*)+$")
        self.assertTrue(advanced.get("caption", "").strip())

        # Any example naming a bundled record must still resolve to that record.
        bundles = {
            page.parent
            for page in board_pages()
            if (page.parent / advanced["src"]).is_file()
        }
        for example in examples:
            with self.subTest(example=example):
                self.assertEqual(".sgf", Path(example["src"]).suffix.lower())
        if bundles:
            for bundle in bundles:
                assert_valid_local_board(self, advanced, bundle)

    def test_readme_covers_the_documented_capability_boundaries(self):
        # Topic terms, not ordered phrases: rewording the prose is fine, but
        # silently dropping a documented boundary is not.
        section = " ".join(self.readme_section().split())
        for topic in (
            "Sabaki",
            "variations",
            "leaf bundle",
            "`move`",
            "`path`",
            "`C`",
            "plain text",
            "no persistence",
            "no third-party requests",
            "Giscus",
        ):
            with self.subTest(topic=topic):
                self.assertIn(topic, section)

    def test_readme_links_the_vendored_license_and_provenance(self):
        local_links = set(
            re.findall(
                r"\]\((assets/vendor/besogo/[^)]+)\)",
                self.readme_section(),
            )
        )
        self.assertEqual(
            {
                "assets/vendor/besogo/UPSTREAM.md",
                "assets/vendor/besogo/LICENSE",
            },
            local_links,
        )
        for target in local_links:
            self.assertTrue((ROOT / target).is_file(), target)


if __name__ == "__main__":
    unittest.main()
