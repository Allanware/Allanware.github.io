import hashlib
from html import unescape
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.check_site import check_site
from scripts.validate_interaction_ids import read_front_matter


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "content/blog/go-game-review-2026-07-26"
PAGE = BUNDLE / "index.en.md"
SGF = BUNDLE / "2026-7-26.sgf"
PRO_SGF = BUNDLE / "2026-7-26_pro.sgf"
EXPECTED_SGF_SHA256 = (
    "829cceb4e5cc25b2d6a97104a76958c7431d98377e33d5d3c0031940bd158427"
)
EXPECTED_PRO_SGF_SHA256 = (
    "4522758078cf8a367e446f981a2f52d3f9f5a91e75e0dc960da38b7100802363"
)
SHORTCODE_PATTERN = re.compile(r"{{<\s*go-board\s+(?P<params>.*?)\s*>}}", re.DOTALL)
ATTRIBUTE_PATTERN = re.compile(r'([a-zA-Z][\w-]*)="([^"]*)"')


def go_board_shortcodes(text: str) -> list[dict[str, str]]:
    return [
        dict(ATTRIBUTE_PATTERN.findall(match.group("params")))
        for match in SHORTCODE_PATTERN.finditer(text)
    ]


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


class GoGameReviewBundleTests(unittest.TestCase):
    def test_sgf_is_the_unmodified_supplied_record(self):
        self.assertTrue(SGF.is_file(), f"missing supplied SGF at {SGF}")
        payload = SGF.read_bytes()
        self.assertEqual(2703, len(payload))
        self.assertEqual(EXPECTED_SGF_SHA256, hashlib.sha256(payload).hexdigest())

    def test_pro_sgf_is_the_unmodified_supplied_record(self):
        self.assertTrue(PRO_SGF.is_file(), f"missing supplied SGF at {PRO_SGF}")
        payload = PRO_SGF.read_bytes()
        self.assertEqual(4770, len(payload))
        self.assertEqual(
            EXPECTED_PRO_SGF_SHA256,
            hashlib.sha256(payload).hexdigest(),
        )

    def test_page_keeps_its_identity_and_three_valid_local_boards(self):
        self.assertTrue(PAGE.is_file(), f"missing English page at {PAGE}")
        self.assertEqual(
            "go-game-review-2026-07-26",
            read_front_matter(PAGE).get("interactionId"),
        )
        boards = go_board_shortcodes(PAGE.read_text(encoding="utf-8"))
        self.assertEqual(
            [
                ("2026-7-26.sgf", "64"),
                ("2026-7-26.sgf", "80"),
                ("2026-7-26_pro.sgf", "36"),
            ],
            [(board.get("src"), board.get("move")) for board in boards],
        )
        self.assertEqual(
            [
                "2026-7-26.sgf — position after move 64.",
                "2026-7-26.sgf — position after move 80.",
                "2026-7-26_pro.sgf — position after move 36.",
            ],
            [board.get("caption") for board in boards],
        )
        for board in boards:
            with self.subTest(board=board):
                assert_valid_local_board(self, board, BUNDLE)

    def test_page_renders_its_local_boards_with_drafts_enabled(self):
        boards = go_board_shortcodes(PAGE.read_text(encoding="utf-8"))
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
            rendered_path = public / "p/go-game-review-2026-07-26/index.html"
            self.assertTrue(
                rendered_path.is_file(),
                "Go review was not rendered with --buildDrafts",
            )
            rendered = rendered_path.read_text(encoding="utf-8")
            for attributes in boards:
                selectors = set(attributes) & {"move", "path"}
                selector_kind = next(iter(selectors), "move")
                selector_value = attributes.get(selector_kind, "0")
                with self.subTest(attributes=attributes):
                    self.assertIn(
                        f'data-selector-kind="{selector_kind}"',
                        rendered,
                    )
                    self.assertIn(
                        f'data-selector-value="{selector_value}"',
                        rendered,
                    )
                    self.assertIn(attributes["caption"], unescape(rendered))
                    published_sgf = (
                        public / "p/go-game-review-2026-07-26"
                        / attributes["src"]
                    )
                    self.assertEqual(
                        (BUNDLE / attributes["src"]).read_bytes(),
                        published_sgf.read_bytes(),
                    )

            figure_ids = re.findall(
                r'<figure id="([^"]+)" class="go-board" data-go-board',
                rendered,
            )
            self.assertEqual(3, len(figure_ids))
            self.assertEqual(3, len(set(figure_ids)))


class GoBoardAuthoringDocumentationTests(unittest.TestCase):
    def test_readme_examples_and_capability_boundaries_are_maintainable(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        section_match = re.search(
            r"^## Interactive Go boards\n(?P<body>.*?)(?=^## |\Z)",
            readme,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section = section_match.group("body")
        normalized = " ".join(section.split())

        examples = go_board_shortcodes(section)
        advanced = next(
            (example for example in examples if "path" in example),
            None,
        )
        self.assertIsNotNone(advanced, "document an exact-path shortcode example")
        self.assertTrue(advanced.get("path"))
        assert_valid_local_board(self, advanced, BUNDLE)

        for pattern in (
            r"Sabaki.*variations.*marks",
            r"authored first SGF node.*`N`.*first-child node transitions.*all nodes.*not moves.*`B`.*1-based child",
            r"`C`.*rendered as plain text.*Markdown.*not formatted",
            r"Try.*local.*no persistence",
            r"no third-party requests.*Giscus.*post-level.*move-level multi-user.*deferred",
        ):
            with self.subTest(pattern=pattern):
                self.assertRegex(normalized, pattern)

        local_links = set(
            re.findall(r"\]\((assets/vendor/besogo/[^)]+)\)", section)
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
