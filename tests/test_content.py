import datetime
import hashlib
import re
import unittest
from pathlib import Path
from types import MappingProxyType

from scripts.validate_interaction_ids import read_front_matter


ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "content" / "blog"
PROJECTS = ROOT / "content" / "projects"
BEYOND_THE_CLOUD = PROJECTS / "beyond-the-cloud"
BEYOND_THE_CLOUD_POST = BEYOND_THE_CLOUD / "index.en.md"
BEYOND_THE_CLOUD_BODY_SHA256 = (
    "41f562021e10b1f920db5e759f53deb148e6ac1ac7e5e007944f8ccbf10315d4"
)
BEYOND_THE_CLOUD_RESOURCE_SHA256 = MappingProxyType(
    {
        "beyond_the_cloud.v5.pdf": (
            "03b5d6396154e0af4953413c4ab3c45c6fd166536791c8d3c6af4dce48fc7ab1"
        ),
    }
)
LEKYTHOS = BLOG / "lekythos-a-shape"
LEKYTHOS_POST = LEKYTHOS / "index.en.md"
LEKYTHOS_BODY_SHA256 = (
    "7cb9a015bf0169b413ba62cf2f71787a2a3904e214a88821b06da273a8f03ccd"
)
LEKYTHOS_RESOURCE_SHA256 = MappingProxyType(
    {
        "front.jpeg": (
            "6d4061fafcffbbfc0ab32efb5bdbe8205ea8e807bcc045cfb7f30cfbbc58bbef"
        ),
        "detail.jpeg": (
            "9b1c451ffe9a27a627a1b9928dea93acdd8b29a9ab4e336b01c1a92c3fbf619d"
        ),
        "inner.jpg": (
            "cde5187ad3bb75c727bcc7c07af8f3551255b1f91ca32c66882df1b3e6e3137b"
        ),
    }
)
ISTANBUL = BLOG / "the-miracle-of-istanbul"
ISTANBUL_POST = ISTANBUL / "index.en.md"
ISTANBUL_BODY_SHA256 = (
    "36b1f8db990e41699b997f5c1fa678311452634ec421d1bc9be5adc248330a30"
)
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
ISTANBUL_RESOURCE_SHA256 = MappingProxyType(
    {
        "2021-03-04-The-Miracle-of-Istanbul.Rmd": (
            "d5121f097ef4d919da720446ef9b3731709b67ef4553bbea4bcfa19095822121"
        ),
        "unnamed-chunk-3-1.png": (
            "81ca7666b1451017fddf2eab5296305ede3d04cebcac3d84eda59f915a595870"
        ),
        "unnamed-chunk-3-2.png": (
            "0b8643a9d9b46d88b2da7ca77bd59de398d866db00ac44df1e924a6e1a587b39"
        ),
        "timeline.png": (
            "c07bfcc78a936044936dcd66345ce68e760951587ea86b855ba94c98df77a570"
        ),
        "unnamed-chunk-9-1.png": (
            "215f79c8a85d197bdfe76ee82d596cf44d52e990daedfc9090f21b18922d6563"
        ),
        "unnamed-chunk-10-1.png": (
            "34d66e9c7c39fc5213144ed76e761d6a96d091ba8ba03f798f963a251e6db7d2"
        ),
        "unnamed-chunk-11-1.png": (
            "05fe572bfd687468ec12381721bc3509dca1b4f98529b611e3d97f8d5474042e"
        ),
        "unnamed-chunk-12-1.png": (
            "7aeeda8db92ab490edf0e5ea840f76e164bfeafbc89593efa8512631ee7472a9"
        ),
        "unnamed-chunk-12-2.png": (
            "e9fef5bc7bfa2a8b9462e1a4f6043e12d27547d2990388b8cf31c4750ac37fd7"
        ),
        "unnamed-chunk-12-3.png": (
            "0556a3c7f103f424cba0b9aed29ad41c7d410ecd49378d5557cf41d3b2cdee8f"
        ),
        "unnamed-chunk-12-4.png": (
            "654b374d18eadafa2defde70e572576bc029c403785396b7d3a68194503c5f79"
        ),
        "unnamed-chunk-13-1.png": (
            "ad6910dbe98ca71741087bf4d1e63ce853b7f8a083ecb8b72f79aedb4864d941"
        ),
        "unnamed-chunk-13-2.png": (
            "925611c1ee5027d658c7b9ae2d3ad06b5744f21e97a77b28fd216dbb875238da"
        ),
        "unnamed-chunk-13-3.png": (
            "a6f735c91fc8cb9ca7d64904ddea10d79839c798da5b48a780197ec05ba571ae"
        ),
        "unnamed-chunk-13-4.png": (
            "b9dda389a13226920ba4613c3d68d60d7e2203bc070fdb2814ac096c75027969"
        ),
        "unnamed-chunk-14-1.png": (
            "09f5006b83fb7ab5b16355181165bafc1f80dd77b4cf5ad31fd3114d413815e2"
        ),
        "unnamed-chunk-14-2.png": (
            "d523adb64a9c07d9f4afc7efceab6ea790d5105e7af9e22aaa0bc317fe7e425f"
        ),
        "unnamed-chunk-15-1.png": (
            "30c82e5816d56860cd923e09cf2a072f03e305e0675117cecf5b8183971dba08"
        ),
        "unnamed-chunk-15-2.png": (
            "dacdf46524af7f8755c110b393c9ea4975f91312cc934198b56fd2d4088660d0"
        ),
        "unnamed-chunk-16-1.png": (
            "d319136d3c3ada008f03720f8e52516437e9d85ef949fb1ffa8420ced5eed51a"
        ),
        "unnamed-chunk-16-2.png": (
            "26796fdf5f730f699b35341e1489e876056edc12742d69bb700356643f63ad48"
        ),
    }
)
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


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class MigratedContentTests(unittest.TestCase):
    def test_beyond_the_cloud_bundle(self):
        front_matter = read_front_matter(BEYOND_THE_CLOUD_POST)

        self.assertEqual(
            set(front_matter),
            {
                "title",
                "date",
                "lastmod",
                "draft",
                "tags",
                "interactionId",
                "projectStatus",
            },
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
        self.assertEqual("past", front_matter["projectStatus"])

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
        self.assertEqual(
            BEYOND_THE_CLOUD_BODY_SHA256,
            sha256(article.encode("utf-8")),
        )

        resources = {
            path.name for path in BEYOND_THE_CLOUD.iterdir() if path != BEYOND_THE_CLOUD_POST
        }
        self.assertEqual(resources, set(BEYOND_THE_CLOUD_RESOURCE_SHA256))
        for resource_name, expected_sha256 in BEYOND_THE_CLOUD_RESOURCE_SHA256.items():
            copied = (BEYOND_THE_CLOUD / resource_name).read_bytes()
            self.assertGreater(len(copied), 0)
            self.assertEqual(expected_sha256, sha256(copied))

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
        self.assertEqual(
            LEKYTHOS_BODY_SHA256,
            sha256(article.encode("utf-8")),
        )

        resources = {
            path.name for path in LEKYTHOS.iterdir() if path != LEKYTHOS_POST
        }
        self.assertEqual(resources, set(LEKYTHOS_RESOURCE_SHA256))
        for image_name, expected_sha256 in LEKYTHOS_RESOURCE_SHA256.items():
            with self.subTest(image=image_name):
                copied = (LEKYTHOS / image_name).read_bytes()
                self.assertGreater(len(copied), 0)
                self.assertEqual(expected_sha256, sha256(copied))

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
        self.assertEqual(17, len(AUTO_CAPTION_LINE.findall(article)))
        with self.subTest("auto-caption blockquotes end before following content"):
            self.assertEqual([], UNTERMINATED_AUTO_CAPTION.findall(article))
        with self.subTest("redundant picture labels are removed"):
            self.assertEqual([], PICTURE_LABEL_LINE.findall(article))
        for image_name, alt in ISTANBUL_IMAGE_ALTS:
            with self.subTest(image=image_name):
                self.assertEqual(article.count(f"![{alt}]({image_name})"), 1)
        self.assertEqual(
            article.count(
                "[Download the R Markdown source]"
                "(2021-03-04-The-Miracle-of-Istanbul.Rmd)"
            ),
            1,
        )
        self.assertEqual(
            ISTANBUL_BODY_SHA256,
            sha256(article.encode("utf-8")),
        )

        resources = {
            path.name for path in ISTANBUL.iterdir() if path != ISTANBUL_POST
        }
        self.assertEqual(resources, set(ISTANBUL_RESOURCE_SHA256))
        self.assertNotIn("cover.png", resources)
        self.assertNotIn("3-3.jpeg", resources)
        for resource_name, expected_sha256 in ISTANBUL_RESOURCE_SHA256.items():
            with self.subTest(resource=resource_name):
                copied = (ISTANBUL / resource_name).read_bytes()
                self.assertGreater(len(copied), 0)
                self.assertEqual(expected_sha256, sha256(copied))


if __name__ == "__main__":
    unittest.main()
