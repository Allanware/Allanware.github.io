import datetime
import unittest
from pathlib import Path

from scripts.validate_interaction_ids import read_front_matter


ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "content" / "blog"
BEYOND_THE_CLOUD = BLOG / "beyond-the-cloud"
BEYOND_THE_CLOUD_POST = BEYOND_THE_CLOUD / "index.en.md"
BEYOND_THE_CLOUD_SOURCE = ROOT / "beyond-the-cloud.md"
BEYOND_THE_CLOUD_PDF = BEYOND_THE_CLOUD / "beyond_the_cloud.v5.pdf"
BEYOND_THE_CLOUD_SOURCE_PDF = (
    ROOT / "writings-images" / "beyond_the_cloud.v5.pdf"
)


def body(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    delimiter = source.splitlines()[0]
    return source.split(delimiter, 2)[2]


def expected_beyond_the_cloud_body() -> str:
    expected = body(BEYOND_THE_CLOUD_SOURCE)
    transformations = (
        (
            "# Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts\n\n",
            "",
        ),
        ("# Abstract", "## Abstract"),
        ("# Poster", "## Poster"),
        (
            "![poster](../../_media/writings-images/beyond_the_cloud.v5.pdf)",
            "[View or download the poster (PDF, 3.7 MB)]"
            "(beyond_the_cloud.v5.pdf)",
        ),
    )
    for original, replacement in transformations:
        expected = expected.replace(original, replacement, 1)
    return expected


class MigratedContentTests(unittest.TestCase):
    def test_beyond_the_cloud_bundle(self):
        front_matter = read_front_matter(BEYOND_THE_CLOUD_POST)

        self.assertEqual(
            set(front_matter),
            {"title", "date", "lastmod", "draft", "tags", "interactionId"},
        )
        self.assertEqual(
            front_matter["title"],
            "Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts",
        )
        self.assertEqual(front_matter["interactionId"], "beyond-the-cloud")
        self.assertEqual(
            front_matter["tags"],
            ["visualization", "perception", "research"],
        )
        self.assertEqual(front_matter["date"], datetime.date(2024, 5, 30))
        self.assertEqual(front_matter["lastmod"], datetime.date(2024, 5, 30))
        self.assertIs(front_matter["draft"], False)

        article = body(BEYOND_THE_CLOUD_POST)
        self.assertNotIn(
            "# Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts",
            article,
        )
        self.assertIn("## Abstract", article)
        self.assertIn("## Poster", article)
        self.assertNotIn("![poster]", article)
        self.assertIn(
            "[View or download the poster (PDF, 3.7 MB)]"
            "(beyond_the_cloud.v5.pdf)",
            article.splitlines(),
        )
        self.assertEqual(article, expected_beyond_the_cloud_body())

        resources = {
            path.name for path in BEYOND_THE_CLOUD.iterdir() if path != BEYOND_THE_CLOUD_POST
        }
        self.assertEqual(resources, {"beyond_the_cloud.v5.pdf"})
        copied_pdf = BEYOND_THE_CLOUD_PDF.read_bytes()
        self.assertGreater(len(copied_pdf), 0)
        self.assertEqual(copied_pdf, BEYOND_THE_CLOUD_SOURCE_PDF.read_bytes())


if __name__ == "__main__":
    unittest.main()
