import datetime
import re
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
LEKYTHOS = BLOG / "lekythos-a-shape"
LEKYTHOS_POST = LEKYTHOS / "index.en.md"
LEKYTHOS_SOURCE = ROOT / "lekythos-a-shape.md"
LEKYTHOS_IMAGES = ("front.jpeg", "detail.jpeg", "inner.jpg")
ISTANBUL = BLOG / "the-miracle-of-istanbul"
ISTANBUL_POST = ISTANBUL / "index.en.md"
ISTANBUL_SOURCE = ROOT / "the-miracle-of-istanbul.md"
ISTANBUL_IMAGE_ALTS = (
    (
        "unnamed-chunk-3-1.png",
        "Starting-eleven market values for AC Milan and Liverpool",
    ),
    (
        "unnamed-chunk-3-2.png",
        "Ten highest-valued players across both starting elevens",
    ),
    ("timeline.png", "Timeline of the 2005 Champions League final"),
    ("unnamed-chunk-9-1.png", "First-half shot map for AC Milan and Liverpool"),
    ("unnamed-chunk-10-1.png", "Second-half shot map for Liverpool and AC Milan"),
    ("unnamed-chunk-11-1.png", "Extra-time shot map for Liverpool and AC Milan"),
    (
        "unnamed-chunk-12-1.png",
        "Picture 1: AC Milan passing map for minutes 1 through 24",
    ),
    (
        "unnamed-chunk-12-2.png",
        "Picture 2: AC Milan passing map after minute 24",
    ),
    (
        "unnamed-chunk-12-3.png",
        "Picture 3: Liverpool passing map for minutes 1 through 24",
    ),
    (
        "unnamed-chunk-12-4.png",
        "Picture 4: Liverpool passing map after minute 24",
    ),
    (
        "unnamed-chunk-13-1.png",
        "Picture 1: AC Milan passing network during the six-minute spell",
    ),
    (
        "unnamed-chunk-13-2.png",
        "Picture 2: AC Milan individual passes during the six-minute spell",
    ),
    (
        "unnamed-chunk-13-3.png",
        "Picture 3: Liverpool passing network during the six-minute spell",
    ),
    (
        "unnamed-chunk-13-4.png",
        "Picture 4: Liverpool individual passes during the six-minute spell",
    ),
    (
        "unnamed-chunk-14-1.png",
        "Picture 1: Liverpool defensive actions during the six-minute spell",
    ),
    (
        "unnamed-chunk-14-2.png",
        "Picture 2: AC Milan defensive actions during the six-minute spell",
    ),
    ("unnamed-chunk-15-1.png", "Picture 1: AC Milan average first-half positions"),
    ("unnamed-chunk-15-2.png", "Picture 2: Liverpool average first-half positions"),
    (
        "unnamed-chunk-16-1.png",
        "Picture 1: AC Milan average early second-half positions",
    ),
    (
        "unnamed-chunk-16-2.png",
        "Picture 2: Liverpool average early second-half positions",
    ),
)
ISTANBUL_RESOURCES = {
    "2021-03-04-The-Miracle-of-Istanbul.Rmd",
    *(image for image, _alt in ISTANBUL_IMAGE_ALTS),
}
AUTO_CAPTION_LINE = re.compile(r"^> \*\[auto-caption\].*$", re.MULTILINE)
UNTERMINATED_AUTO_CAPTION = re.compile(
    r"^> \*\[auto-caption\].*\n(?=[^\n])",
    re.MULTILINE,
)
PICTURE_LABEL_LINE = re.compile(r"^_picture [1-4]_$", re.MULTILINE)


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


def expected_lekythos_body() -> str:
    expected = body(LEKYTHOS_SOURCE)
    transformations = (
        ("# Shapes and Functions of the Lekythos\n\n", ""),
        (
            '<img src="front.jpeg" alt="front view" width="400"/>\n\n'
            "__Front view (note its size from the other lekythos)__",
            '\n{{< bundle-image src="front.jpeg" '
            'alt="Front view of the lekythos beside another vessel" '
            'width="400" >}}',
        ),
        (
            '<img src="detail.jpeg" alt="detailed view" width="400"/>\n\n'
            "__A detailed view on the painting__",
            '{{< bundle-image src="detail.jpeg" '
            'alt="Detail of the painted scene" width="400" >}}',
        ),
        (
            '<img src="inner.jpg" alt="the innovation inside" width="200"/>',
            '\n{{< bundle-image src="inner.jpg" '
            'alt="Interior vessel inside the lekythos" width="200" >}}',
        ),
        ("http:/www.beazley.ox.ac.uk", "http://www.beazley.ox.ac.uk"),
    )
    for original, replacement in transformations:
        expected = expected.replace(original, replacement, 1)
    return expected


def expected_istanbul_body() -> str:
    expected = body(ISTANBUL_SOURCE)
    expected = expected.replace("# The Miracle of Istanbul\n\n", "", 1)
    expected = expected.replace("../../_media/writings-images/", "")
    expected = expected.replace("<!-- -->\n\n", "\n\n")
    expected = expected.replace("<!-- -->\n", "\n\n")
    expected, separated_caption_count = UNTERMINATED_AUTO_CAPTION.subn(
        lambda match: match.group(0) + "\n",
        expected,
    )
    if separated_caption_count != 15:
        raise AssertionError(
            "expected exactly 15 auto-caption separators, "
            f"found {separated_caption_count}"
        )
    expected, removed_picture_label_count = re.subn(
        r"^_picture [1-4]_\n\n",
        "",
        expected,
        flags=re.MULTILINE,
    )
    if removed_picture_label_count != 14:
        raise AssertionError(
            "expected exactly 14 redundant picture labels, "
            f"found {removed_picture_label_count}"
        )
    for image_name, alt in ISTANBUL_IMAGE_ALTS:
        expected = expected.replace(
            f"![]({image_name})",
            f"![{alt}]({image_name})",
            1,
        )
    expected = expected.replace(
        "- [code](2021-03-04-The-Miracle-of-Istanbul.Rmd)",
        "- [Download the R Markdown source]"
        "(2021-03-04-The-Miracle-of-Istanbul.Rmd)",
        1,
    )
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

    def test_lekythos_bundle(self):
        front_matter = read_front_matter(LEKYTHOS_POST)

        self.assertEqual(
            set(front_matter),
            {"title", "date", "lastmod", "draft", "tags", "interactionId"},
        )
        self.assertEqual(
            front_matter["title"],
            "Shapes and Functions of the Lekythos",
        )
        self.assertEqual(front_matter["interactionId"], "lekythos-a-shape")
        self.assertEqual(front_matter["tags"], ["Greek", "Pottery"])
        self.assertEqual(front_matter["date"], datetime.date(2022, 11, 8))
        self.assertEqual(front_matter["lastmod"], datetime.date(2023, 11, 5))
        self.assertIs(front_matter["draft"], False)

        article = body(LEKYTHOS_POST)
        self.assertNotIn("# Shapes and Functions of the Lekythos", article)
        self.assertNotIn("<img", article)
        shortcode_calls = [
            '{{< bundle-image src="front.jpeg" '
            'alt="Front view of the lekythos beside another vessel" '
            'width="400" >}}',
            '{{< bundle-image src="detail.jpeg" '
            'alt="Detail of the painted scene" width="400" >}}',
            '{{< bundle-image src="inner.jpg" '
            'alt="Interior vessel inside the lekythos" width="200" >}}',
        ]
        self.assertEqual(article.count("{{< bundle-image "), 3)
        for call in shortcode_calls:
            self.assertEqual(article.count(call), 1)
        self.assertIn("http://www.beazley.ox.ac.uk", article)
        self.assertEqual(article, expected_lekythos_body())

        resources = {
            path.name for path in LEKYTHOS.iterdir() if path != LEKYTHOS_POST
        }
        self.assertEqual(resources, set(LEKYTHOS_IMAGES))
        for image_name in LEKYTHOS_IMAGES:
            with self.subTest(image=image_name):
                copied = (LEKYTHOS / image_name).read_bytes()
                source = (ROOT / "writings-images" / image_name).read_bytes()
                self.assertGreater(len(copied), 0)
                self.assertEqual(copied, source)

    def test_istanbul_bundle(self):
        front_matter = read_front_matter(ISTANBUL_POST)

        self.assertEqual(
            set(front_matter),
            {"title", "date", "lastmod", "draft", "tags", "interactionId"},
        )
        self.assertEqual(front_matter["title"], "The Miracle of Istanbul")
        self.assertEqual(front_matter["interactionId"], "the-miracle-of-istanbul")
        self.assertEqual(
            front_matter["tags"],
            ["football", "data visualization", "r"],
        )
        self.assertEqual(front_matter["date"], datetime.date(2021, 3, 4))
        self.assertEqual(front_matter["lastmod"], datetime.date(2023, 11, 5))
        self.assertIs(front_matter["draft"], False)

        article = body(ISTANBUL_POST)
        self.assertNotIn("\n# The Miracle of Istanbul", article)
        self.assertNotIn("../../_media", article)
        self.assertNotIn("<!-- -->", article)
        self.assertNotIn("![](", article)
        source_article = body(ISTANBUL_SOURCE)
        self.assertEqual(
            15,
            len(UNTERMINATED_AUTO_CAPTION.findall(source_article)),
        )
        self.assertEqual(
            AUTO_CAPTION_LINE.findall(source_article),
            AUTO_CAPTION_LINE.findall(article),
        )
        self.assertEqual(14, len(PICTURE_LABEL_LINE.findall(source_article)))
        with self.subTest("auto-caption blockquotes end before following content"):
            self.assertEqual([], UNTERMINATED_AUTO_CAPTION.findall(article))
        with self.subTest("redundant picture labels are removed"):
            self.assertEqual([], PICTURE_LABEL_LINE.findall(article))
        self.assertEqual(
            article.count(
                "[Download the R Markdown source]"
                "(2021-03-04-The-Miracle-of-Istanbul.Rmd)"
            ),
            1,
        )
        self.assertEqual(article, expected_istanbul_body())

        resources = {
            path.name for path in ISTANBUL.iterdir() if path != ISTANBUL_POST
        }
        self.assertEqual(resources, ISTANBUL_RESOURCES)
        self.assertNotIn("cover.png", resources)
        self.assertNotIn("3-3.jpeg", resources)
        for resource_name in ISTANBUL_RESOURCES:
            with self.subTest(resource=resource_name):
                copied = (ISTANBUL / resource_name).read_bytes()
                source = (ROOT / "writings-images" / resource_name).read_bytes()
                self.assertGreater(len(copied), 0)
                self.assertEqual(copied, source)


if __name__ == "__main__":
    unittest.main()
