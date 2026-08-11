from datetime import date
import hashlib
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.check_site import check_site
from scripts.validate_interaction_ids import read_front_matter


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "content/blog/go-game-review-2026-07-26"
DRAFT = BUNDLE / "index.en.md"
SGF = BUNDLE / "2026-7-26.sgf"
EXPECTED_SGF_SHA256 = (
    "829cceb4e5cc25b2d6a97104a76958c7431d98377e33d5d3c0031940bd158427"
)


def markdown_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    closing = text.find("\n+++\n", 4)
    if closing == -1:
        raise AssertionError(f"missing closing front-matter delimiter in {path}")
    return text[closing + 5 :]


class GoGameReviewDraftTests(unittest.TestCase):
    def test_sgf_is_the_unmodified_supplied_record(self):
        self.assertTrue(SGF.is_file(), f"missing supplied SGF at {SGF}")
        payload = SGF.read_bytes()
        self.assertEqual(2703, len(payload))
        self.assertEqual(EXPECTED_SGF_SHA256, hashlib.sha256(payload).hexdigest())

    def test_draft_metadata_and_body_are_exact_and_english_only(self):
        self.assertTrue(DRAFT.is_file(), f"missing English draft at {DRAFT}")
        self.assertFalse((BUNDLE / "index.zh.md").exists())
        self.assertEqual(
            {
                "title": "Go Game Review — July 26, 2026",
                "date": date(2026, 8, 10),
                "lastmod": date(2026, 8, 10),
                "draft": True,
                "tags": ["go"],
                "interactionId": "go-game-review-2026-07-26",
            },
            read_front_matter(DRAFT),
        )
        self.assertEqual(
            "\n## First branching point\n\n"
            "At move 64, the record splits into two continuations.\n\n"
            '{{< go-board src="2026-7-26.sgf" move="64" '
            'caption="Position after move 64." >}}\n',
            markdown_body(DRAFT),
        )

    def test_draft_renders_the_selected_local_board_when_drafts_are_enabled(self):
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
                "draft board post was not rendered with --buildDrafts",
            )
            rendered = rendered_path.read_text(encoding="utf-8")
            self.assertIn('data-selector-kind="move"', rendered)
            self.assertIn('data-selector-value="64"', rendered)
            self.assertIn("Position after move 64.", rendered)
            published_sgf = (
                public / "p/go-game-review-2026-07-26/2026-7-26.sgf"
            )
            self.assertEqual(SGF.read_bytes(), published_sgf.read_bytes())
            self.assertFalse(
                (public / "zh/p/go-game-review-2026-07-26/index.html").exists()
            )


class GoBoardAuthoringDocumentationTests(unittest.TestCase):
    def test_readme_documents_the_beginner_authoring_contract(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        section_match = re.search(
            r"^## Interactive Go boards\n(?P<body>.*?)(?=^## |\Z)",
            readme,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section = section_match.group("body")
        normalized_section = " ".join(section.split())

        required_fragments = (
            "Sabaki",
            "index.en.md",
            "index.zh.md",
            "share the same SGF asset",
            'src="game.sgf" move="64" caption="Position after move 64."',
            "`src` and `caption` are required",
            "defaults to move 0",
            "skips non-move nodes",
            "`path=N64B2N3`",
            "BesoGo node counts",
            "1-based branch numbers",
            "mutually exclusive",
            "A/B",
            "`CR`, `TR`, `SQ`, `MA`, `LB`, and `SL`",
            "`B`/`W`",
            "`AB`/`AW`/`AE`",
            "plain-text `C`",
            "Markdown post",
            "language-neutral, bilingual, or omitted",
            "arrows and lines",
            "Markdown inside `C`",
            "`SBKV` and `SBKS`",
            "Previous",
            "Next",
            "Try",
            "Return",
            "local and ephemeral",
            "no persistence",
            "no third-party requests",
            "Giscus",
            "post-level",
            "move-level multi-user discussion",
            "separate app or backend",
            "assets/vendor/besogo/UPSTREAM.md",
            "assets/vendor/besogo/LICENSE",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, normalized_section)


if __name__ == "__main__":
    unittest.main()
