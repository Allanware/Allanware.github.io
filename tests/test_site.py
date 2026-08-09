from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]


def build_site(destination: Path, base_url: str, *extra_arguments: str) -> None:
    # Markup tests stay unminified; Task 13 passes --minify in its production matrix.
    command = [
        "hugo",
        "--source", str(ROOT),
        "--destination", str(destination),
        "--baseURL", base_url,
        "--cleanDestinationDir",
        "--panicOnWarning",
        "--noBuildLock",
        "--cacheDir", str(destination.parent / "cache"),
        "--gc",
        *extra_arguments,
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)


def read_html(public: Path, relative: str) -> str:
    return (public / relative).read_text(encoding="utf-8")


class PrimaryNavigationParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_primary = False
        self.active_href: str | None = None
        self.active_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        values = dict(attributes)
        if tag == "nav" and "data-primary-navigation" in values:
            self.in_primary = True
        elif self.in_primary and tag == "a" and "data-primary-link" in values:
            self.active_href = values.get("href")
            self.active_text = []

    def handle_data(self, data: str) -> None:
        if self.active_href is not None:
            self.active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.active_href is not None:
            self.links.append((self.active_href, "".join(self.active_text).strip()))
            self.active_href = None
            self.active_text = []
        elif tag == "nav" and self.in_primary:
            self.in_primary = False


def primary_navigation(html: str) -> list[tuple[str, str]]:
    parser = PrimaryNavigationParser()
    parser.feed(html)
    return parser.links


class MarkupReviewParser(HTMLParser):
    VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.active_link_attributes: dict[str, str | None] | None = None
        self.active_link_text: list[str] = []
        self.links: list[tuple[str, dict[str, str | None]]] = []
        self.inline_images: list[tuple[bool, bool]] = []
        self.figures_in_paragraph: list[bool] = []
        self.zoom_control_ids: list[str] = []

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        values = dict(attributes)
        classes = set((values.get("class") or "").split())
        if tag == "a":
            self.active_link_attributes = values
            self.active_link_text = []
        elif tag == "img" and "inline-image" in classes:
            self.inline_images.append(("p" in self.stack, "figure" in self.stack))
        elif tag == "figure":
            self.figures_in_paragraph.append("p" in self.stack)
        elif tag == "input" and "image-zoom-toggle" in classes:
            control_id = values.get("id")
            if control_id is not None:
                self.zoom_control_ids.append(control_id)
        if tag not in self.VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_data(self, data: str) -> None:
        if self.active_link_attributes is not None:
            self.active_link_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.active_link_attributes is not None:
            self.links.append(
                ("".join(self.active_link_text).strip(), self.active_link_attributes)
            )
            self.active_link_attributes = None
            self.active_link_text = []
        if tag in self.stack:
            reverse_index = self.stack[::-1].index(tag)
            del self.stack[len(self.stack) - reverse_index - 1 :]


class GeneratedSiteTests(unittest.TestCase):
    def test_localized_core_routes_exist(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            expected = [
                "index.html",
                "blog/index.html",
                "tags/index.html",
                "zh/index.html",
                "zh/blog/index.html",
                "zh/tags/index.html",
            ]
            for relative in expected:
                self.assertTrue((public / relative).is_file(), relative)
            self.assertIn("Wenxuan Zhao", (public / "index.html").read_text(encoding="utf-8"))
            self.assertIn("赵文轩", (public / "zh/index.html").read_text(encoding="utf-8"))

    def test_chrome_is_localized_and_uses_browser_color_preference(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            english = read_html(public, "index.html")
            chinese = read_html(public, "zh/index.html")
            self.assertEqual(
                [("/", "Home"), ("/blog/", "Posts"), ("/tags/", "Tags")],
                primary_navigation(english),
            )
            self.assertEqual(
                [("/zh/", "首页"), ("/zh/blog/", "文章"), ("/zh/tags/", "标签")],
                primary_navigation(chinese),
            )
            self.assertIn('<html lang="en-US"', english)
            self.assertIn('<html lang="zh-CN"', chinese)
            self.assertIn('name="color-scheme" content="light dark"', english)
            self.assertIn('name="referrer" content="strict-origin-when-cross-origin"', english)
            self.assertIn('media="(prefers-color-scheme: light)"', english)
            self.assertIn('media="(prefers-color-scheme: dark)"', english)
            self.assertNotIn("theme-toggle", english)
            primary = re.search(
                r'<nav[^>]*data-primary-navigation[^>]*>(.*?)</nav>',
                english,
                re.DOTALL,
            )
            self.assertIsNotNone(primary)
            self.assertNotIn("language-switcher", primary.group(1))
            self.assertIn('class="language-switcher"', english)

    def test_markdown_hooks_are_safe_valid_unique_and_keyboard_accessible(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            bundle = content / "blog" / "markup-review"
            bundle.mkdir(parents=True)
            (bundle / "index.en.md").write_text(
                """+++
title = "Markup review"
date = 2026-08-09
draft = false
interactionId = "markup-review"
+++

Inline prose ![Inline diagram](diagram.svg) continues.

![Block diagram](diagram.svg)

![Repeated block diagram](diagram.svg)

## Review heading

[Unsafe destination](javascript:alert(1) "x\\\" onmouseover=\\\"alert(2)")
""",
                encoding="utf-8",
            )
            (bundle / "diagram.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                '<rect width="10" height="10"/></svg>',
                encoding="utf-8",
            )
            public = temporary_root / "public"
            build_site(
                public,
                "https://example.test/",
                "--contentDir",
                str(content),
            )
            article = read_html(public, "p/markup-review/index.html")
            parser = MarkupReviewParser()
            parser.feed(article)

            unsafe_link = next(
                attributes
                for text, attributes in parser.links
                if text == "Unsafe destination"
            )
            with self.subTest("unsafe URL is sanitized"):
                self.assertNotIn(
                    "javascript:",
                    (unsafe_link.get("href") or "").lower(),
                )
                self.assertEqual("#ZgotmplZ", unsafe_link.get("href"))
            with self.subTest("title cannot inject an event attribute"):
                self.assertNotIn("onmouseover", unsafe_link)
                self.assertEqual(
                    r'x\" onmouseover=\"alert(2)',
                    unsafe_link.get("title"),
                )
            with self.subTest("inline image remains inside prose"):
                self.assertEqual([(True, False)], parser.inline_images)
            with self.subTest("block image figures are paragraph siblings"):
                self.assertEqual([False, False], parser.figures_in_paragraph)
                self.assertNotRegex(article, r"<p>\s*<figure")
            with self.subTest("repeated block image controls are unique"):
                self.assertEqual(2, len(parser.zoom_control_ids))
                self.assertEqual(
                    len(parser.zoom_control_ids),
                    len(set(parser.zoom_control_ids)),
                )

            css = (ROOT / "assets" / "css" / "site.css").read_text(encoding="utf-8")
            with self.subTest("keyboard focus reveals TOC links"):
                self.assertIn(".toc-nav:focus-within a", css)
                self.assertRegex(
                    css,
                    r"\.toc-nav a:focus-visible\s*\{[^}]*color: var\(--text-color-primary\)",
                )
                self.assertRegex(
                    css,
                    r"\.toc-nav a:focus-visible::before\s*\{[^}]*background-color: var\(--text-color-primary\)",
                )


if __name__ == "__main__":
    unittest.main()
