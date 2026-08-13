import hashlib
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
BUNDLE = ROOT / "content/blog/go-game-review-2026-07-26"
PAGE = BUNDLE / "index.en.md"
ZH_PAGE = BUNDLE / "index.zh.md"
HAN_PATTERN = re.compile(r"[一-鿿]")
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

    def test_translation_shares_identity_and_mirrors_the_english_boards(self):
        self.assertTrue(ZH_PAGE.is_file(), f"missing Chinese page at {ZH_PAGE}")
        english_front_matter = read_front_matter(PAGE)
        chinese_front_matter = read_front_matter(ZH_PAGE)
        self.assertEqual(
            english_front_matter.get("interactionId"),
            chinese_front_matter.get("interactionId"),
        )
        self.assertEqual(
            english_front_matter.get("draft"),
            chinese_front_matter.get("draft"),
        )
        self.assertRegex(str(chinese_front_matter.get("title", "")), HAN_PATTERN)

        english_boards = go_board_shortcodes(PAGE.read_text(encoding="utf-8"))
        chinese_boards = go_board_shortcodes(ZH_PAGE.read_text(encoding="utf-8"))
        self.assertEqual(
            [(board.get("src"), board.get("move")) for board in english_boards],
            [(board.get("src"), board.get("move")) for board in chinese_boards],
        )
        for board in chinese_boards:
            with self.subTest(board=board):
                assert_valid_local_board(self, board, BUNDLE)
                caption = board.get("caption", "")
                self.assertRegex(caption, HAN_PATTERN)
                self.assertNotIn("position after move", caption)

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
            figures = list(RENDERED_GO_BOARD_FIGURE_PATTERN.finditer(rendered))
            self.assertEqual(3, len(figures))

            base_path = urlsplit(base_url).path.rstrip("/")
            published_page_path = "/p/go-game-review-2026-07-26"
            figure_ids = []
            figure_sgf_urls = []
            for attributes, figure in zip(boards, figures, strict=True):
                selector_kind = next(
                    (
                        selector
                        for selector in ("move", "path")
                        if selector in attributes
                    ),
                    "move",
                )
                selector_value = attributes.get(selector_kind, "0")
                with self.subTest(attributes=attributes):
                    figure_attributes = dict(
                        ATTRIBUTE_PATTERN.findall(figure.group("opening"))
                    )
                    figure_id = figure_attributes.get("id")
                    self.assertIsNotNone(figure_id)
                    self.assertRegex(figure_id, r"^go-board-[0-9a-f]{12}$")
                    figure_ids.append(figure_id)

                    expected_sgf_url = (
                        f"{base_path}{published_page_path}/{attributes['src']}"
                    )
                    self.assertEqual(
                        expected_sgf_url,
                        figure_attributes.get("data-sgf-url"),
                    )
                    figure_sgf_urls.append(figure_attributes["data-sgf-url"])
                    self.assertEqual(
                        selector_kind,
                        figure_attributes.get("data-selector-kind"),
                    )
                    self.assertEqual(
                        selector_value,
                        figure_attributes.get("data-selector-value"),
                    )
                    self.assertEqual(
                        [attributes["caption"]],
                        [
                            unescape(caption)
                            for caption in FIGCAPTION_PATTERN.findall(
                                figure.group(0)
                            )
                        ],
                    )
                    published_sgf = public / figure_attributes[
                        "data-sgf-url"
                    ].removeprefix(base_path).lstrip("/")
                    self.assertEqual(
                        (BUNDLE / attributes["src"]).read_bytes(),
                        published_sgf.read_bytes(),
                    )

            self.assertEqual(3, len(figure_ids))
            self.assertEqual(3, len(set(figure_ids)))
            self.assertEqual(
                [
                    f"{base_path}{published_page_path}/2026-7-26.sgf",
                    f"{base_path}{published_page_path}/2026-7-26.sgf",
                    f"{base_path}{published_page_path}/2026-7-26_pro.sgf",
                ],
                figure_sgf_urls,
            )


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
