from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "assets/vendor/besogo"
PINNED_COMMIT = "4f03a3a04bc632c49ca9b494cbcad5c7cfb3f6b2"
REQUIRED_JS = {
    "besogo.js",
    "boardDisplay.js",
    "coord.js",
    "editor.js",
    "gameRoot.js",
    "loadSgf.js",
    "parseSgf.js",
    "svgUtil.js",
}


class GoBoardVendorTests(unittest.TestCase):
    def test_besogo_vendor_is_pinned_minimal_and_image_free(self):
        self.assertEqual(
            REQUIRED_JS,
            {path.name for path in (VENDOR / "js").glob("*.js")},
        )
        self.assertEqual(
            {"board-flat.css"},
            {path.name for path in (VENDOR / "css").glob("*.css")},
        )
        self.assertFalse((VENDOR / "img").exists())

        license_text = (VENDOR / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2015-2018 Ye Wang", license_text)

        provenance = (VENDOR / "UPSTREAM.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/yewang/besogo", provenance)
        self.assertIn(PINNED_COMMIT, provenance)


if __name__ == "__main__":
    unittest.main()
