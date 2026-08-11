import base64
import hashlib
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from scripts.check_site import check_site


ROOT = Path(__file__).resolve().parents[1]
BRANDING_CONFIG = "hugo.toml,tests/fixtures/branding.toml"
FIXTURE_TITLE_EN = "Fixture Site"
FIXTURE_TITLE_ZH = "测试站点"
FIXTURE_CONTACT_EMAIL = "editor@example.test"
FIXTURE_GITHUB_URL = "https://github.example.test/fixture"
FIXTURE_SCHOLAR_URL = "https://scholar.example.test/fixture"


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
        "--environment", "production",
        *extra_arguments,
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)


def run_hugo(
    destination: Path,
    base_url: str,
    *extra_arguments: str,
) -> subprocess.CompletedProcess[str]:
    command = [
        "hugo",
        "--source", str(ROOT),
        "--destination", str(destination),
        "--baseURL", base_url,
        "--cleanDestinationDir",
        "--panicOnWarning",
        "--noBuildLock",
        "--cacheDir", str(destination.parent / "cache"),
        *extra_arguments,
    ]
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def command_output(result: subprocess.CompletedProcess[str]) -> str:
    return "\n".join(part for part in (result.stdout, result.stderr) if part)


def read_html(public: Path, relative: str) -> str:
    return (public / relative).read_text(encoding="utf-8")


def png_dimensions(path: Path) -> tuple[int, int]:
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise AssertionError(f"not a PNG: {path}")
    return tuple(int.from_bytes(payload[offset : offset + 4], "big") for offset in (16, 20))


def alternate_link_entries(html: str) -> list[tuple[str, str]]:
    return re.findall(
        r'<link[^>]+rel="alternate"[^>]+hreflang="([^"]+)"[^>]+href="([^"]+)"',
        html,
    )


def alternate_links(html: str) -> set[tuple[str, str]]:
    return set(alternate_link_entries(html))


def css_root_custom_properties(
    css: str,
    *,
    scheme: str | None = None,
) -> dict[str, str]:
    if scheme is None:
        search_area = css.split("@media", 1)[0]
        match = re.search(r":root\s*\{([^}]*)\}", search_area, re.DOTALL)
    else:
        match = re.search(
            rf"@media\s*\(prefers-color-scheme:\s*{re.escape(scheme)}\)"
            r"\s*\{(?:\s|/\*.*?\*/)*:root\s*\{([^}]*)\}",
            css,
            re.DOTALL,
        )
    if match is None:
        return {}
    return {
        name: value.strip().lower()
        for name, value in re.findall(
            r"(--[a-z0-9-]+)\s*:\s*([^;]+);",
            match.group(1),
        )
    }


def wcag_relative_luminance(color: str) -> float:
    match = re.fullmatch(r"#([0-9a-fA-F]{6})", color)
    if match is None:
        raise ValueError(f"expected a six-digit hex color, got {color!r}")
    channels = [
        int(match.group(1)[offset : offset + 2], 16) / 255
        for offset in (0, 2, 4)
    ]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def wcag_contrast_ratio(foreground: str, background: str) -> float:
    luminances = sorted(
        (
            wcag_relative_luminance(foreground),
            wcag_relative_luminance(background),
        ),
        reverse=True,
    )
    return (luminances[0] + 0.05) / (luminances[1] + 0.05)


# Chroma classes that never paint a glyph over the code background: the block
# chrome, line wrappers, and the line-number and whitespace helpers the site
# does not render.
CHROMA_NON_TEXT_CLASSES = frozenset(
    {"bg", "cl", "hl", "line", "ln", "lnlinks", "lnt", "lntable", "lntd", "w"}
)


def expand_hex_color(value: str) -> str:
    """Normalize a CSS color, expanding the three-digit hex shorthand."""
    value = value.strip().lower()
    match = re.fullmatch(r"#([0-9a-f]{3})", value)
    return f"#{''.join(channel * 2 for channel in match.group(1))}" if match else value


def semantic_color_tokens() -> dict[str, dict[str, str]]:
    """Resolve the theme and site custom properties for each color scheme."""
    theme_css = (
        ROOT / "themes/hugo-bearneo/layouts/partials/style.html"
    ).read_text(encoding="utf-8")
    site_css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
    return {
        "light": {
            **css_root_custom_properties(theme_css),
            **css_root_custom_properties(site_css),
            **css_root_custom_properties(site_css, scheme="light"),
        },
        "dark": {
            **css_root_custom_properties(theme_css),
            **css_root_custom_properties(theme_css, scheme="dark"),
            **css_root_custom_properties(site_css),
            **css_root_custom_properties(site_css, scheme="dark"),
        },
    }


def chroma_rules(css: str, scheme: str) -> dict[str, tuple[str | None, str | None]]:
    """Map Chroma class to its (color, background-color) for one color scheme."""
    sections = [
        (match.group(1), match.end())
        for match in re.finditer(
            r"@media\s*\(prefers-color-scheme:\s*(light|dark)\)",
            css,
        )
    ]
    rules: dict[str, tuple[str | None, str | None]] = {}
    for index, (name, start) in enumerate(sections):
        if name != scheme:
            continue
        end = sections[index + 1][1] if index + 1 < len(sections) else len(css)
        for selector, body in re.findall(
            r"\.chroma(?:\s+\.([a-zA-Z0-9-]+))?\s*\{([^}]*)\}",
            css[start:end],
        ):
            color = re.search(r"(?<![-\w])color:\s*([^;}]+)", body)
            background = re.search(r"background-color:\s*([^;}]+)", body)
            rules[selector] = (
                expand_hex_color(color.group(1)) if color else None,
                expand_hex_color(background.group(1)) if background else None,
            )
    return rules


class MetadataParser(HTMLParser):
    DESCRIPTION_SELECTORS = {
        ("name", "description"): "description",
        ("property", "og:description"): "og:description",
        ("name", "twitter:description"): "twitter:description",
        ("itemprop", "description"): "schema:description",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.descriptions: dict[str, list[str]] = {
            name: [] for name in self.DESCRIPTION_SELECTORS.values()
        }

    def handle_starttag(
        self,
        tag: str,
        attributes: list[tuple[str, str | None]],
    ) -> None:
        if tag != "meta":
            return
        values = dict(attributes)
        content = values.get("content")
        if content is None:
            return
        for selector, name in self.DESCRIPTION_SELECTORS.items():
            attribute, expected = selector
            if values.get(attribute) == expected:
                self.descriptions[name].append(content)


def metadata_descriptions(html: str) -> dict[str, list[str]]:
    parser = MetadataParser()
    parser.feed(html)
    return parser.descriptions


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


class HeaderNavigationParser(HTMLParser):
    VOID_ELEMENTS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int | None]] = []
        self.rows: list[list[tuple[str, bool, tuple[str, ...]]]] = []

    def handle_starttag(
        self,
        tag: str,
        attributes: list[tuple[str, str | None]],
    ) -> None:
        values = dict(attributes)
        classes = tuple(sorted((values.get("class") or "").split()))
        if self.stack:
            _, parent_row = self.stack[-1]
            if parent_row is not None:
                self.rows[parent_row].append(
                    (tag, "data-primary-navigation" in values, classes)
                )

        row_index = None
        if tag == "div" and "header-navigation" in classes:
            row_index = len(self.rows)
            self.rows.append([])
        if tag not in self.VOID_ELEMENTS:
            self.stack.append((tag, row_index))

    def handle_endtag(self, tag: str) -> None:
        tags = [entry[0] for entry in self.stack]
        if tag in tags:
            reverse_index = tags[::-1].index(tag)
            del self.stack[len(self.stack) - reverse_index - 1 :]


def header_navigation_signatures(
    html: str,
) -> list[list[tuple[str, bool, tuple[str, ...]]]]:
    parser = HeaderNavigationParser()
    parser.feed(html)
    return parser.rows


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
        self.figure_images: list[list[dict[str, str | None]]] = []
        self.zoom_control_ids: list[str] = []
        self.paragraph_texts: list[list[str]] = []
        self.paragraphs_in_blockquote: list[bool] = []
        self.emphasis_texts: list[list[str]] = []

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        values = dict(attributes)
        classes = set((values.get("class") or "").split())
        if tag == "p":
            self.paragraph_texts.append([])
            self.paragraphs_in_blockquote.append("blockquote" in self.stack)
        elif tag == "em":
            self.emphasis_texts.append([])
        if tag == "a":
            self.active_link_attributes = values
            self.active_link_text = []
        elif tag == "img" and "inline-image" in classes:
            self.inline_images.append(("p" in self.stack, "figure" in self.stack))
        elif tag == "figure":
            self.figures_in_paragraph.append("p" in self.stack)
            self.figure_images.append([])
        elif tag == "img" and "figure" in self.stack:
            self.figure_images[-1].append(values)
        elif tag == "input" and "image-zoom-toggle" in classes:
            control_id = values.get("id")
            if control_id is not None:
                self.zoom_control_ids.append(control_id)
        if tag not in self.VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_data(self, data: str) -> None:
        if "p" in self.stack:
            self.paragraph_texts[-1].append(data)
        if "em" in self.stack:
            self.emphasis_texts[-1].append(data)
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
    def test_build_site_requests_the_production_environment(self):
        with TemporaryDirectory() as temporary, patch.object(subprocess, "run") as run:
            build_site(
                Path(temporary) / "public",
                "https://example.test/example-blog/",
                "--minify",
            )

        command = run.call_args.args[0]
        environment_index = command.index("--environment")
        self.assertEqual("production", command[environment_index + 1])

    def test_production_build_is_valid_at_root_and_project_subpath(self):
        with TemporaryDirectory() as temporary:
            for name, base_url in (
                ("root", "https://example.github.io/"),
                ("project", "https://example.github.io/example-blog/"),
            ):
                with self.subTest(build=name):
                    public = Path(temporary) / name
                    build_site(public, base_url, "--minify")

                    self.assertEqual([], check_site(public, base_url))
                    self.assertTrue((public / ".nojekyll").is_file())

                    html_documents = sorted(public.rglob("*.html"))
                    xml_documents = sorted(public.rglob("*.xml"))
                    self.assertTrue(html_documents)
                    self.assertTrue(xml_documents)

                    for document in xml_documents:
                        with self.subTest(build=name, xml=document.relative_to(public)):
                            ET.parse(document)

    def test_seo_uses_only_real_translations(self):
        with TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "fixture"
            build_site(
                fixture,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            english = read_html(fixture, "p/shared-article/index.html")
            chinese = read_html(fixture, "zh/p/shared-article/index.html")
            english_posts = read_html(fixture, "blog/index.html")
            chinese_posts = read_html(fixture, "zh/blog/index.html")
            self.assertNotIn("data-post-count", english_posts)
            self.assertIn('data-count-one="{count} post"', english_posts)
            self.assertIn('data-count-many="{count} posts"', english_posts)
            self.assertNotIn("data-post-count", chinese_posts)
            self.assertIn('data-count-one="{count} 篇文章"', chinese_posts)
            self.assertIn('data-count-many="{count} 篇文章"', chinese_posts)
            expected = {
                ("en-US", "https://example.test/p/shared-article/"),
                ("zh-CN", "https://example.test/zh/p/shared-article/"),
                ("x-default", "https://example.test/p/shared-article/"),
            }
            for html in [english, chinese]:
                self.assertEqual(expected, alternate_links(html))
                self.assertEqual(3, len(alternate_link_entries(html)))
            self.assertIn('class="language-switcher"', english)
            self.assertIn('href="/zh/p/shared-article/"', english)
            self.assertIn('href="/p/shared-article/"', chinese)
            for html in [english, chinese]:
                self.assertIn('src="/p/shared-article/diagram.svg"', html)
                self.assertIn('href="/p/shared-article/notes.txt"', html)
            self.assertTrue((fixture / "p/shared-article/diagram.svg").is_file())
            self.assertTrue((fixture / "p/shared-article/notes.txt").is_file())
            chinese_only = read_html(fixture, "zh/p/chinese-only/index.html")
            self.assertEqual(set(), alternate_links(chinese_only))
            self.assertIn(
                '<link rel="canonical" href="https://example.test/zh/p/chinese-only/">',
                chinese_only,
            )
            word_count = re.search(r'data-word-count="(\d+)"', chinese_only)
            self.assertIsNotNone(word_count)
            self.assertEqual(26, int(word_count.group(1)))
            description = re.search(
                r'<meta name="description" content="([^"]*)"',
                chinese_only,
            )
            self.assertIsNotNone(description)
            self.assertEqual("天地玄黄宇宙洪荒日月盈", description.group(1).strip())
            self.assertNotIn("尾标", description.group(1))
            chinese_descriptions = metadata_descriptions(chinese_only)
            self.assertEqual(
                {"天地玄黄宇宙洪荒日月盈"},
                {
                    value
                    for values in chinese_descriptions.values()
                    for value in values
                },
            )
            self.assertTrue(
                all(len(values) == 1 for values in chinese_descriptions.values())
            )
            english_tags = read_html(fixture, "tags/index.html")
            chinese_tags = read_html(fixture, "zh/tags/index.html")
            self.assertIn("#fixture", english_tags)
            self.assertNotIn("#测试", english_tags)
            self.assertIn("#测试", chinese_tags)
            self.assertNotIn("#fixture", chinese_tags)
            self.assertIn('href="/zh/tags/%E6%B5%8B%E8%AF%95/"', chinese_tags)
            self.assertTrue((fixture / "zh/tags/测试/index.html").is_file())
            chinese_term = read_html(fixture, "zh/tags/测试/index.html")
            self.assertIn("共享文章", chinese_term)
            self.assertIn("仅中文文章", chinese_term)
            self.assertNotIn("Shared article", chinese_term)
            english_same_term = read_html(fixture, "tags/same-spelling/index.html")
            chinese_same_term = read_html(
                fixture,
                "zh/tags/same-spelling/index.html",
            )
            for term_html in [english_same_term, chinese_same_term]:
                self.assertNotIn('class="language-switcher"', term_html)
                self.assertEqual(set(), alternate_links(term_html))
            self.assertIn("Shared article", english_same_term)
            self.assertNotIn("仅中文文章", english_same_term)
            self.assertIn("仅中文文章", chinese_same_term)
            self.assertNotIn("Shared article", chinese_same_term)
            sitemap_index = ET.parse(fixture / "sitemap.xml").getroot()
            locations = {
                node.text for node in sitemap_index.findall("{*}sitemap/{*}loc")
            }
            self.assertEqual(
                {
                    "https://example.test/en/sitemap.xml",
                    "https://example.test/zh/sitemap.xml",
                },
                locations,
            )
            english_sitemap = ET.parse(fixture / "en/sitemap.xml").getroot()
            shared_entry = next(
                node for node in english_sitemap.findall("{*}url")
                if node.findtext("{*}loc")
                == "https://example.test/p/shared-article/"
            )
            sitemap_alternate_entries = [
                (link.attrib["hreflang"], link.attrib["href"])
                for link in shared_entry.findall(
                    "{http://www.w3.org/1999/xhtml}link"
                )
            ]
            self.assertEqual(expected, set(sitemap_alternate_entries))
            self.assertEqual(3, len(sitemap_alternate_entries))
            chinese_sitemap = ET.parse(fixture / "zh/sitemap.xml").getroot()
            chinese_shared_entry = next(
                node for node in chinese_sitemap.findall("{*}url")
                if node.findtext("{*}loc")
                == "https://example.test/zh/p/shared-article/"
            )
            chinese_sitemap_alternate_entries = [
                (link.attrib["hreflang"], link.attrib["href"])
                for link in chinese_shared_entry.findall(
                    "{http://www.w3.org/1999/xhtml}link"
                )
            ]
            self.assertEqual(expected, set(chinese_sitemap_alternate_entries))
            self.assertEqual(3, len(chinese_sitemap_alternate_entries))
            chinese_only_entry = next(
                node for node in chinese_sitemap.findall("{*}url")
                if node.findtext("{*}loc")
                == "https://example.test/zh/p/chinese-only/"
            )
            self.assertEqual(
                [],
                chinese_only_entry.findall(
                    "{http://www.w3.org/1999/xhtml}link"
                ),
            )
            for sitemap, location in [
                (english_sitemap, "https://example.test/tags/same-spelling/"),
                (
                    chinese_sitemap,
                    "https://example.test/zh/tags/same-spelling/",
                ),
            ]:
                term_entry = next(
                    node for node in sitemap.findall("{*}url")
                    if node.findtext("{*}loc") == location
                )
                self.assertEqual(
                    [],
                    term_entry.findall(
                        "{http://www.w3.org/1999/xhtml}link"
                    ),
                )

            project = Path(temporary) / "project"
            build_site(
                project,
                "https://example.test/example-blog/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            project_english = read_html(
                project,
                "p/shared-article/index.html",
            )
            project_chinese = read_html(
                project,
                "zh/p/shared-article/index.html",
            )
            project_expected = {
                (
                    "en-US",
                    "https://example.test/example-blog/p/shared-article/",
                ),
                (
                    "zh-CN",
                    "https://example.test/example-blog/zh/p/shared-article/",
                ),
                (
                    "x-default",
                    "https://example.test/example-blog/p/shared-article/",
                ),
            }
            for html in [project_english, project_chinese]:
                self.assertEqual(project_expected, alternate_links(html))
                self.assertEqual(3, len(alternate_link_entries(html)))
                self.assertIn(
                    'src="/example-blog/p/shared-article/diagram.svg"',
                    html,
                )
                self.assertIn(
                    'href="/example-blog/p/shared-article/notes.txt"',
                    html,
                )
            self.assertIn(
                '<link rel="canonical" '
                'href="https://example.test/example-blog/zh/p/shared-article/">',
                project_chinese,
            )
            project_sitemap_index = ET.parse(project / "sitemap.xml").getroot()
            self.assertEqual(
                {
                    "https://example.test/example-blog/en/sitemap.xml",
                    "https://example.test/example-blog/zh/sitemap.xml",
                },
                {
                    node.text
                    for node in project_sitemap_index.findall(
                        "{*}sitemap/{*}loc"
                    )
                },
            )
            project_sitemaps = {
                "en": ET.parse(project / "en/sitemap.xml").getroot(),
                "zh": ET.parse(project / "zh/sitemap.xml").getroot(),
            }
            project_shared_locations = {
                "en": "https://example.test/example-blog/p/shared-article/",
                "zh": "https://example.test/example-blog/zh/p/shared-article/",
            }
            for language, sitemap in project_sitemaps.items():
                with self.subTest(project_sitemap=language):
                    for node in sitemap.findall("{*}url"):
                        self.assertTrue(
                            node.findtext("{*}loc").startswith(
                                "https://example.test/example-blog/"
                            )
                        )
                        for link in node.findall(
                            "{http://www.w3.org/1999/xhtml}link"
                        ):
                            self.assertTrue(
                                link.attrib["href"].startswith(
                                    "https://example.test/example-blog/"
                                )
                            )
                    shared = next(
                        node for node in sitemap.findall("{*}url")
                        if node.findtext("{*}loc")
                        == project_shared_locations[language]
                    )
                    project_sitemap_alternates = [
                        (link.attrib["hreflang"], link.attrib["href"])
                        for link in shared.findall(
                            "{http://www.w3.org/1999/xhtml}link"
                        )
                    ]
                    self.assertEqual(
                        project_expected,
                        set(project_sitemap_alternates),
                    )
                    self.assertEqual(3, len(project_sitemap_alternates))
                    same_spelling_location = (
                        "https://example.test/example-blog/"
                        + ("" if language == "en" else "zh/")
                        + "tags/same-spelling/"
                    )
                    same_spelling = next(
                        node for node in sitemap.findall("{*}url")
                        if node.findtext("{*}loc") == same_spelling_location
                    )
                    self.assertEqual(
                        [],
                        same_spelling.findall(
                            "{http://www.w3.org/1999/xhtml}link"
                        ),
                    )
            self.assertTrue((project / "zh/tags/测试/index.html").is_file())

    def test_giscus_uses_shared_strict_threads_and_validated_configuration(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            fixture = temporary_root / "fixture"
            build_site(
                fixture,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            english = read_html(fixture, "p/shared-article/index.html")
            chinese = read_html(fixture, "zh/p/shared-article/index.html")
            chinese_only = read_html(fixture, "zh/p/chinese-only/index.html")
            shared_attributes = (
                'data-repo="fixture-owner/fixture-repository"',
                'data-repo-id="R_fixture"',
                'data-category="Fixture category"',
                'data-category-id="DIC_fixture"',
                'data-mapping="specific"',
                'data-term="post:shared-article"',
                'data-strict="1"',
                'data-reactions-enabled="1"',
                'data-emit-metadata="0"',
                'data-input-position="bottom"',
                'data-theme="preferred_color_scheme"',
                'data-loading="lazy"',
                'crossorigin="anonymous"',
            )
            for language, html, locale in (
                ("English", english, "en"),
                ("Chinese", chinese, "zh-CN"),
            ):
                with self.subTest(language=language):
                    self.assertEqual(1, html.count("https://giscus.app/client.js"))
                    self.assertNotIn("http://giscus.app/client.js", html)
                    for attribute in shared_attributes:
                        self.assertIn(attribute, html)
                    self.assertIn(f'data-lang="{locale}"', html)
                    self.assertRegex(html, r'<script[^>]*\sasync(?:\s|>)')
            self.assertEqual(1, chinese_only.count("https://giscus.app/client.js"))
            self.assertIn('data-term="post:chinese-only"', chinese_only)
            self.assertNotIn('data-term="post:shared-article"', chinese_only)

            padded = temporary_root / "padded"
            build_site(
                padded,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/padded-giscus.toml",
                "--contentDir", "tests/fixtures/content",
            )
            padded_english = read_html(
                padded,
                "p/shared-article/index.html",
            )
            padded_chinese = read_html(
                padded,
                "zh/p/shared-article/index.html",
            )
            for html, locale in (
                (padded_english, "en"),
                (padded_chinese, "zh-CN"),
            ):
                self.assertIn(
                    'data-repo="fixture-owner/fixture-repository"',
                    html,
                )
                self.assertIn('data-repo-id="R_fixture"', html)
                self.assertIn('data-category="Fixture category"', html)
                self.assertIn('data-category-id="DIC_fixture"', html)
                self.assertIn(f'data-lang="{locale}"', html)
                self.assertNotIn("arbitrary-invalid-locale", html)

    def test_kudos_uses_shared_entities_accessible_ssr_and_hashed_modules(self):
        module_pattern = re.compile(
            r'<script(?=[^>]*\btype="module")'
            r'(?=[^>]*\bsrc="([^"]*kudos[^"]*)")'
            r'(?=[^>]*\bintegrity="([^"]+)")[^>]*></script>'
        )
        root_pattern = re.compile(r'<div\b[^>]*\sdata-kudos(?:\s|>)')

        def assert_one_widget(
            public: Path,
            relative: str,
            entity: str,
            expected_base_path: str,
        ) -> str:
            html = read_html(public, relative)
            self.assertEqual(1, len(root_pattern.findall(html)))
            self.assertEqual(
                1,
                html.count(f'data-kudos-entity="{entity}"'),
            )
            self.assertEqual(1, html.count("data-kudos-button"))
            self.assertEqual(1, html.count('data-kudos-state="loading"'))
            self.assertIn('aria-busy="true"', html)
            self.assertRegex(
                html,
                r'<span[^>]*data-kudos-count[^>]*>—</span>',
            )
            self.assertNotIn('aria-pressed=', html)
            self.assertRegex(html, r'<div[^>]*data-kudos[^>]*hidden')
            self.assertRegex(
                html,
                r'<button[^>]*data-kudos-button[^>]*disabled',
            )

            modules = module_pattern.findall(html)
            self.assertEqual(1, len(modules))
            source, integrity = modules[0]
            self.assertRegex(
                source,
                rf'^{re.escape(expected_base_path)}js/'
                r'kudos\.[0-9a-f]{64}\.mjs$',
            )
            source_path = urlsplit(source).path
            self.assertTrue(source_path.startswith(expected_base_path))
            asset_relative = source_path[len(expected_base_path):]
            asset = public / asset_relative
            self.assertTrue(asset.is_file(), source)
            expected_integrity = "sha256-" + base64.b64encode(
                hashlib.sha256(asset.read_bytes()).digest()
            ).decode("ascii")
            self.assertEqual(expected_integrity, integrity)
            return html

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            fixture = temporary_root / "fixture"
            build_site(
                fixture,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            english = assert_one_widget(
                fixture,
                "p/shared-article/index.html",
                "post:shared-article",
                "/",
            )
            chinese = assert_one_widget(
                fixture,
                "zh/p/shared-article/index.html",
                "post:shared-article",
                "/",
            )
            chinese_only = assert_one_widget(
                fixture,
                "zh/p/chinese-only/index.html",
                "post:chinese-only",
                "/",
            )
            self.assertNotIn(
                'data-kudos-entity="post:shared-article"',
                chinese_only,
            )
            self.assertIn('data-add-label="Upvote this post"', english)
            self.assertIn('data-add-label="赞同这篇文章"', chinese)

            project = temporary_root / "project"
            build_site(
                project,
                "https://example.test/example-blog/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            assert_one_widget(
                project,
                "p/shared-article/index.html",
                "post:shared-article",
                "/example-blog/",
            )
            assert_one_widget(
                project,
                "zh/p/shared-article/index.html",
                "post:shared-article",
                "/example-blog/",
            )

    def test_kudos_endpoint_configuration_is_strict_and_graceful(self):
        invalid_configs = (
            "incomplete-interactions.toml",
            "invalid-endpoint-relative.toml",
            "invalid-endpoint-whitespace.toml",
            "invalid-endpoint-http.toml",
            "invalid-endpoint-path.toml",
            "invalid-endpoint-query.toml",
            "invalid-endpoint-fragment.toml",
            "invalid-endpoint-port.toml",
            "invalid-endpoint-port-zero.toml",
            "invalid-endpoint-port-high.toml",
            "invalid-endpoint-credentials.toml",
            "invalid-endpoint-host.toml",
            "invalid-endpoint-label.toml",
            "invalid-endpoint-unicode-host.toml",
            "invalid-kudos-enabled.toml",
            "invalid-kudos-types.toml",
            "invalid-kudos-container-scalar.toml",
            "invalid-kudos-container-list.toml",
            "disabled-kudos.toml",
        )
        valid_configs = {
            "valid-endpoint-https.toml": "https://worker.example",
            "valid-endpoint-port-min.toml": "https://worker.example:1",
            "valid-endpoint-port-max.toml": "https://worker.example:65535/",
            "trailing-slash-endpoint.toml": "https://worker.example/",
            "valid-endpoint-whitespace.toml": "https://worker.example/",
            "valid-endpoint-localhost.toml": "http://localhost:65535/",
            "valid-endpoint-loopback.toml": "http://127.0.0.1/",
        }

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            invalid_content = temporary_root / "invalid-content"
            shutil.copytree(ROOT / "tests/fixtures/content", invalid_content)
            second_article = invalid_content / "blog/second-article"
            second_article.mkdir()
            (second_article / "index.en.md").write_text(
                '+++\ntitle = "Second article"\ndate = 2026-08-09\n'
                'draft = false\ninteractionId = "second-article"\n+++\n\nBody.\n',
                encoding="utf-8",
            )
            for index, config in enumerate(invalid_configs):
                with self.subTest(invalid_config=config):
                    destination = temporary_root / f"invalid-{index}"
                    build_site(
                        destination,
                        "https://example.test/",
                        "--config", f"hugo.toml,tests/fixtures/{config}",
                        "--contentDir", str(invalid_content),
                    )
                    html = read_html(
                        destination,
                        "p/shared-article/index.html",
                    )
                    self.assertNotIn("data-kudos", html)
                    self.assertNotIn("js/kudos.", html)
                    home = read_html(destination, "index.html")
                    popular = re.search(
                        r'<section data-home-section="popular">(.*?)</section>',
                        home,
                        re.DOTALL,
                    ).group(1)
                    self.assertIn(
                        "Popular posts are temporarily unavailable",
                        popular,
                    )
                    self.assertNotIn("data-popular-posts", popular)
                    self.assertNotIn("data-popular-candidate", popular)
                    self.assertNotIn("js/popular-posts.", popular)

            for index, (config, endpoint) in enumerate(valid_configs.items()):
                with self.subTest(valid_config=config):
                    destination = temporary_root / f"valid-{index}"
                    build_site(
                        destination,
                        "https://example.test/",
                        "--config", f"hugo.toml,tests/fixtures/{config}",
                        "--contentDir", "tests/fixtures/content",
                    )
                    html = read_html(
                        destination,
                        "p/shared-article/index.html",
                    )
                    self.assertEqual(
                        1,
                        html.count(f'data-kudos-endpoint="{endpoint}"'),
                    )
                    self.assertEqual(
                        1,
                        len(re.findall(
                            r'<div\b[^>]*\sdata-kudos(?:\s|>)',
                            html,
                        )),
                    )
                    self.assertEqual(1, html.count("js/kudos."))

    def test_giscus_suppresses_incomplete_mistyped_and_malformed_configuration(self):
        static_configs = (
            "tests/fixtures/incomplete-interactions.toml",
            "tests/fixtures/invalid-giscus-repo.toml",
            "tests/fixtures/invalid-giscus-whitespace.toml",
            "tests/fixtures/invalid-giscus-enabled.toml",
            "tests/fixtures/invalid-giscus-types.toml",
            "tests/fixtures/invalid-giscus-container-scalar.toml",
            "tests/fixtures/invalid-giscus-container-list.toml",
        )
        invalid_field_values = {
            "enabled-integer": "enabled = 1",
            "repo-integer": "repo = 42",
            "repo-whitespace": 'repo = "   "',
            "repo-missing-owner": 'repo = "/repository"',
            "repo-missing-name": 'repo = "owner/"',
            "repo-extra-slash": 'repo = "owner/repository/extra"',
            "repo-internal-whitespace": 'repo = "owner name/repository"',
            "repo-id-boolean": "repoId = true",
            "repo-id-whitespace": 'repoId = "   "',
            "category-integer": "category = 42",
            "category-whitespace": 'category = "   "',
            "category-id-boolean": "categoryId = true",
            "category-id-whitespace": 'categoryId = "   "',
        }
        defaults = {
            "enabled": "enabled = true",
            "repo": 'repo = "fixture-owner/fixture-repository"',
            "repoId": 'repoId = "R_fixture"',
            "category": 'category = "Fixture category"',
            "categoryId": 'categoryId = "DIC_fixture"',
        }

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            for index, config in enumerate(static_configs):
                with self.subTest(config=config):
                    destination = temporary_root / f"static-{index}"
                    build_site(
                        destination,
                        "https://example.test/",
                        "--config", f"hugo.toml,{config}",
                        "--contentDir", "tests/fixtures/content",
                    )
                    html = read_html(
                        destination,
                        "p/shared-article/index.html",
                    )
                    self.assertNotIn("giscus.app/client.js", html)

            for index, (name, invalid_line) in enumerate(
                invalid_field_values.items()
            ):
                with self.subTest(field_case=name):
                    invalid_key = invalid_line.split(" = ", 1)[0]
                    lines = ["[params.giscus]"]
                    for key, default_line in defaults.items():
                        lines.append(
                            invalid_line if key == invalid_key else default_line
                        )
                    config = temporary_root / f"field-{index}.toml"
                    config.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    destination = temporary_root / f"field-{index}"
                    build_site(
                        destination,
                        "https://example.test/",
                        "--config", f"hugo.toml,{config}",
                        "--contentDir", "tests/fixtures/content",
                    )
                    html = read_html(
                        destination,
                        "p/shared-article/index.html",
                    )
                    self.assertNotIn("giscus.app/client.js", html)

    def test_hugo_rejects_invalid_published_interaction_ids_directly(self):
        cases = (
            (
                "malformed",
                "tests/fixtures/invalid-content",
                "hugo.toml",
                'interactionId "Invalid ID" must match',
            ),
            (
                "non-string",
                "tests/fixtures/nonstring-content",
                "hugo.toml",
                "interactionId must be a string",
            ),
            (
                "overlong",
                "tests/fixtures/overlong-content",
                "hugo.toml",
                "at most 80 characters",
            ),
            (
                "translation-mismatch",
                "tests/fixtures/mismatched-content",
                "hugo.toml",
                "translations must share interactionId",
            ),
            (
                "missing-with-site-fallback",
                "tests/fixtures/missing-id-content",
                "hugo.toml,tests/fixtures/site-id.toml",
                "published articles require interactionId",
            ),
            (
                "missing-with-language-fallback",
                "tests/fixtures/missing-id-content",
                "hugo.toml,tests/fixtures/language-id.toml",
                "published articles require interactionId",
            ),
        )
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            for index, (name, content_dir, config, expected) in enumerate(cases):
                with self.subTest(case=name):
                    result = run_hugo(
                        temporary_root / f"invalid-{index}",
                        "https://example.test/",
                        "--config", config,
                        "--contentDir", content_dir,
                    )
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn(expected, command_output(result))

    def test_interaction_id_boundaries_and_draft_translation_semantics(self):
        malformed = {
            "empty": "",
            "uppercase": "Uppercase",
            "leading-hyphen": "-leading",
            "trailing-hyphen": "trailing-",
            "double-hyphen": "double--hyphen",
        }
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            for index, (name, interaction_id) in enumerate(malformed.items()):
                with self.subTest(malformed=name):
                    content = temporary_root / f"malformed-{index}" / "content"
                    bundle = content / "blog" / "identity-case"
                    bundle.mkdir(parents=True)
                    (bundle / "index.en.md").write_text(
                        f'''+++
title = "Malformed identity"
date = 2026-08-08
draft = false
interactionId = "{interaction_id}"
+++

Fixture.
''',
                        encoding="utf-8",
                    )
                    result = run_hugo(
                        temporary_root / f"malformed-{index}" / "public",
                        "https://example.test/",
                        "--contentDir", str(content),
                    )
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn(
                        "must match ^[a-z0-9]+(?:-[a-z0-9]+)*$",
                        command_output(result),
                    )

            valid_content = temporary_root / "valid-80" / "content"
            valid_bundle = valid_content / "blog" / "valid-80"
            valid_bundle.mkdir(parents=True)
            exact_limit = "a" * 80
            (valid_bundle / "index.en.md").write_text(
                f'''+++
title = "Exact identity limit"
date = 2026-08-08
draft = false
interactionId = "{exact_limit}"
+++

Fixture.
''',
                encoding="utf-8",
            )
            valid_public = temporary_root / "valid-80" / "public"
            valid_result = run_hugo(
                valid_public,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", str(valid_content),
            )
            self.assertEqual(
                0,
                valid_result.returncode,
                command_output(valid_result),
            )
            valid_html = read_html(valid_public, "p/valid-80/index.html")
            self.assertIn(f'data-term="post:{exact_limit}"', valid_html)

            draft_content = temporary_root / "draft" / "content"
            draft_bundle = draft_content / "blog" / "standalone-draft"
            draft_bundle.mkdir(parents=True)
            (draft_bundle / "index.en.md").write_text(
                '''+++
title = "Standalone draft"
date = 2026-08-08
draft = true
+++

Fixture.
''',
                encoding="utf-8",
            )
            draft_public = temporary_root / "draft" / "public"
            draft_result = run_hugo(
                draft_public,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", str(draft_content),
                "--buildDrafts",
            )
            self.assertEqual(
                0,
                draft_result.returncode,
                command_output(draft_result),
            )
            draft_html = read_html(
                draft_public,
                "p/standalone-draft/index.html",
            )
            self.assertNotIn("giscus.app/client.js", draft_html)

            translated = temporary_root / "translated-draft" / "content"
            translated_bundle = translated / "blog" / "translated-draft"
            translated_bundle.mkdir(parents=True)
            (translated_bundle / "index.en.md").write_text(
                '''+++
title = "Published translation"
date = 2026-08-08
draft = false
interactionId = "translated-draft"
+++

Fixture.
''',
                encoding="utf-8",
            )
            (translated_bundle / "index.zh.md").write_text(
                '''+++
title = "翻译草稿"
date = 2026-08-08
draft = true
+++

测试。
''',
                encoding="utf-8",
            )
            translated_result = run_hugo(
                temporary_root / "translated-draft" / "public",
                "https://example.test/",
                "--contentDir", str(translated),
                "--buildDrafts",
            )
            self.assertNotEqual(0, translated_result.returncode)
            self.assertIn(
                "translations must share interactionId",
                command_output(translated_result),
            )

    def test_interaction_identity_is_computed_once_from_page_local_params(self):
        identity_path = ROOT / "layouts/_partials/interaction-id.html"
        self.assertTrue(identity_path.is_file())
        identity = identity_path.read_text(encoding="utf-8")
        article = (ROOT / "layouts/_partials/article.html").read_text(
            encoding="utf-8"
        )
        blog_page = (ROOT / "layouts/blog/page.html").read_text(encoding="utf-8")
        project_page = (ROOT / "layouts/projects/page.html").read_text(
            encoding="utf-8"
        )
        self.assertEqual(1, identity.count("return $result"))
        self.assertRegex(identity, r'isset\s+\$page\.Params\s+"interactionid"')
        self.assertNotRegex(identity, r'\$page\.Param\b')
        self.assertIn("$page.Translations", identity)
        self.assertNotIn("$page.AllTranslations", identity)
        self.assertEqual(1, article.count('partial "interaction-id.html" .'))
        kudos_call = (
            'partial "kudos.html" '
            '(dict "Page" . "Entity" $interactionEntity)'
        )
        giscus_call = (
            'partial "giscus.html" '
            '(dict "Page" . "Entity" $interactionEntity)'
        )
        self.assertEqual(1, article.count(kudos_call))
        self.assertEqual(1, article.count(giscus_call))
        self.assertLess(article.index(kudos_call), article.index(giscus_call))
        for entrypoint in (blog_page, project_page):
            self.assertEqual(1, entrypoint.count('partial "article.html" .'))
            self.assertNotIn('partial "interaction-id.html"', entrypoint)
            self.assertNotIn('partial "kudos.html"', entrypoint)
            self.assertNotIn('partial "giscus.html"', entrypoint)

    def test_hidden_translations_are_not_advertised(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            fixtures = {
                "blog/visible-with-hidden/index.en.md": '''+++
title = "Visible English translation"
date = 2026-08-09
draft = false
interactionId = "visible-with-hidden"
+++

Visible English content.
''',
                "blog/visible-with-hidden/index.zh.md": '''+++
title = "隐藏的中文翻译"
date = 2026-08-09
draft = false
hidden = true
interactionId = "visible-with-hidden"
+++

隐藏的中文内容。
''',
            }
            for relative, source in fixtures.items():
                path = content / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            public = temporary_root / "public"
            build_site(
                public,
                "https://example.test/",
                "--contentDir",
                str(content),
            )
            english = read_html(
                public,
                "p/visible-with-hidden/index.html",
            )
            chinese = read_html(
                public,
                "zh/p/visible-with-hidden/index.html",
            )
            self.assertIn(
                '<link rel="canonical" '
                'href="https://example.test/p/visible-with-hidden/">',
                english,
            )
            self.assertNotIn('<meta name="robots" content="noindex">', english)
            self.assertNotIn('<link rel="canonical"', chinese)
            self.assertEqual(
                1,
                chinese.count(
                    '<meta name="robots" content="noindex">'
                ),
            )
            self.assertNotIn('<link rel="alternate" hreflang=', chinese)
            for html in [english, chinese]:
                self.assertEqual([], alternate_link_entries(html))
                self.assertNotIn('class="language-switcher"', html)

            visible_url = "https://example.test/p/visible-with-hidden/"
            hidden_url = "https://example.test/zh/p/visible-with-hidden/"
            for language in ["en", "zh"]:
                sitemap = ET.parse(
                    public / language / "sitemap.xml"
                ).getroot()
                advertised_urls = {
                    node.findtext("{*}loc")
                    for node in sitemap.findall("{*}url")
                }
                advertised_urls.update(
                    link.attrib["href"]
                    for node in sitemap.findall("{*}url")
                    for link in node.findall(
                        "{http://www.w3.org/1999/xhtml}link"
                    )
                )
                with self.subTest(sitemap_language=language):
                    self.assertNotIn(hidden_url, advertised_urls)
            english_sitemap = ET.parse(public / "en/sitemap.xml").getroot()
            visible_entry = next(
                node for node in english_sitemap.findall("{*}url")
                if node.findtext("{*}loc") == visible_url
            )
            self.assertEqual(
                [],
                visible_entry.findall(
                    "{http://www.w3.org/1999/xhtml}link"
                ),
            )

    def test_rss_is_separate_localized_and_base_path_aware(self):
        with TemporaryDirectory() as temporary:
            for name, base_url, base_path in (
                ("root", "https://example.test/", "/"),
                ("project", "https://example.test/project/", "/project/"),
            ):
                public = Path(temporary) / name
                build_site(
                    public,
                    base_url,
                    "--config",
                    f"{BRANDING_CONFIG},tests/fixtures/interactions.toml",
                    "--contentDir",
                    "tests/fixtures/content",
                )
                english = ET.parse(public / "index.xml").getroot().find("channel")
                chinese = ET.parse(public / "zh/index.xml").getroot().find("channel")
                self.assertIsNotNone(english)
                self.assertIsNotNone(chinese)
                self.assertEqual("en-US", english.findtext("language"))
                self.assertEqual("zh-CN", chinese.findtext("language"))
                self.assertEqual(
                    ["Shared article"],
                    [item.findtext("title") for item in english.findall("item")],
                )
                self.assertCountEqual(
                    ["共享文章", "仅中文文章"],
                    [item.findtext("title") for item in chinese.findall("item")],
                )
                self.assertIn(
                    f"Recent posts from {FIXTURE_TITLE_EN}",
                    english.findtext("description"),
                )
                self.assertIn(
                    f"{FIXTURE_TITLE_ZH}的最新文章",
                    chinese.findtext("description"),
                )

                chinese_home = read_html(public, "zh/index.html")
                self.assertIn(
                    f'href="{base_url}zh/index.xml"',
                    chinese_home,
                )
                self.assertIn(
                    f'href="{base_path}zh/index.xml"',
                    chinese_home,
                )

                for channel, expected_home in (
                    (english, base_url),
                    (chinese, f"{base_url}zh/"),
                ):
                    self.assertEqual(expected_home, channel.findtext("link"))
                    atom_self = channel.find("{http://www.w3.org/2005/Atom}link")
                    self.assertTrue(atom_self.get("href").startswith(base_url))
                    for item in channel.findall("item"):
                        self.assertTrue(item.findtext("link").startswith(base_url))
                        self.assertTrue(item.findtext("guid").startswith(base_url))

    def test_rss_excludes_hidden_posts_before_limiting_and_escapes_once(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            fixtures = {
                "blog/older/index.en.md": '''+++
title = "Visible older post"
date = 2024-01-01
draft = false
interactionId = "rss-visible-older"
+++

Visible older body.
''',
                "blog/newer/index.en.md": '''+++
title = "Visible newer post"
date = 2025-06-01
draft = false
interactionId = "rss-visible-newer"
+++

Visible newer body `p<.001 & "quoted"`.
''',
                "blog/hidden/index.en.md": '''+++
title = "Hidden newest post"
date = 2026-08-09
draft = false
hidden = true
interactionId = "rss-hidden-newest"
+++

Hidden body.
''',
            }
            for relative, source in fixtures.items():
                path = content / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            public = temporary_root / "public"
            build_site(
                public,
                "https://example.test/",
                "--contentDir",
                str(content),
            )
            channel = ET.parse(public / "index.xml").getroot().find("channel")
            items = channel.findall("item")
            titles = [item.findtext("title") for item in items]
            with self.subTest("hidden posts are omitted from the ordered feed"):
                self.assertEqual(
                    ["Visible newer post", "Visible older post"],
                    titles,
                )

            newer = next(
                item for item in items if item.findtext("title") == "Visible newer post"
            )
            description = newer.findtext("description")
            with self.subTest("summary entities are decoded exactly once"):
                self.assertIn('p<.001 & "quoted"', description)
                self.assertNotIn("&lt;", description)
                self.assertNotIn("&amp;", description)

            limited = temporary_root / "limited"
            build_site(
                limited,
                "https://example.test/",
                "--contentDir",
                str(content),
                "--config",
                "hugo.toml,tests/fixtures/rss-limit.toml",
            )
            limited_channel = ET.parse(limited / "index.xml").getroot().find(
                "channel"
            )
            with self.subTest("hidden posts do not consume the RSS limit"):
                self.assertEqual(
                    ["Visible newer post", "Visible older post"],
                    [
                        item.findtext("title")
                        for item in limited_channel.findall("item")
                    ],
                )





    def test_bundle_image_shortcode_rejects_invalid_arguments(self):
        fixtures = (
            (
                "omitted-src",
                '{{< bundle-image alt="Diagram" width="400" >}}',
                "bundle-image: resource.*not found",
            ),
            (
                "omitted-alt",
                '{{< bundle-image src="diagram.svg" width="400" >}}',
                "bundle-image: alt must be non-empty",
            ),
            (
                "omitted-width",
                '{{< bundle-image src="diagram.svg" alt="Diagram" >}}',
                "bundle-image: width.*positive integer",
            ),
            (
                "missing-resource",
                '{{< bundle-image src="missing.jpg" alt="Missing" width="400" >}}',
                "bundle-image: resource.*missing.jpg.*not found",
            ),
            (
                "empty-alt",
                '{{< bundle-image src="diagram.svg" alt="  " width="400" >}}',
                "bundle-image: alt must be non-empty",
            ),
            (
                "zero-width",
                '{{< bundle-image src="diagram.svg" alt="Diagram" width="0" >}}',
                "bundle-image: width.*positive integer",
            ),
            (
                "noninteger-width",
                '{{< bundle-image src="diagram.svg" alt="Diagram" width="wide" >}}',
                "bundle-image: width.*positive integer",
            ),
        )

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            for name, shortcode, message_pattern in fixtures:
                with self.subTest(case=name):
                    content = temporary_root / name / "content"
                    bundle = content / "blog" / "invalid-bundle-image"
                    bundle.mkdir(parents=True)
                    (bundle / "index.en.md").write_text(
                        f'''+++
title = "Invalid bundle image"
date = 2026-08-09
draft = false
interactionId = "invalid-bundle-image"
+++

{shortcode}
''',
                        encoding="utf-8",
                    )
                    (bundle / "diagram.svg").write_text(
                        '<svg xmlns="http://www.w3.org/2000/svg" '
                        'viewBox="0 0 10 10"></svg>',
                        encoding="utf-8",
                    )
                    result = subprocess.run(
                        [
                            "hugo",
                            "--source", str(ROOT),
                            "--destination", str(temporary_root / name / "public"),
                            "--baseURL", "https://example.test/",
                            "--contentDir", str(content),
                            "--panicOnWarning",
                            "--noBuildLock",
                            "--cacheDir", str(temporary_root / name / "cache"),
                        ],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    output = result.stderr + result.stdout
                    self.assertRegex(output, message_pattern)
                    self.assertNotRegex(
                        output,
                        r"(?i)nil pointer|index out of range|can't evaluate field",
                    )

    def test_markdown_and_bundle_image_controls_have_unique_ids(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            bundle = content / "blog" / "mixed-image-renderers"
            bundle.mkdir(parents=True)
            (bundle / "index.en.md").write_text(
                '''+++
title = "Mixed image renderers"
date = 2026-08-09
draft = false
interactionId = "mixed-image-renderers"
+++

![Markdown diagram](diagram.svg)

{{< bundle-image src="diagram.svg" alt="Shortcode diagram" width="400" >}}
''',
                encoding="utf-8",
            )
            (bundle / "diagram.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 10 10"></svg>',
                encoding="utf-8",
            )
            public = temporary_root / "public"
            build_site(
                public,
                "https://example.test/",
                "--contentDir",
                str(content),
            )
            article = read_html(public, "p/mixed-image-renderers/index.html")
            parser = MarkupReviewParser()
            parser.feed(article)

            self.assertEqual(2, len(parser.zoom_control_ids))
            self.assertEqual(2, len(set(parser.zoom_control_ids)))

    def test_markdown_bundle_resources_resolve_encoded_paths_and_preserve_suffixes(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            bundle = content / "blog" / "resource-suffixes"
            bundle.mkdir(parents=True)
            for language, title, body in (
                (
                    "en",
                    "Resource suffixes",
                    "![Diagram](my%20diagram.svg?mode=print#preview)\n\n"
                    "![Mini diagram](diagram.svg#minipic)\n\n"
                    "[Notes](my%20notes.txt?download=1#details)",
                ),
                (
                    "zh",
                    "资源后缀",
                    "![图表](my%20diagram.svg?mode=print#preview)\n\n"
                    "![小图](diagram.svg#minipic)\n\n"
                    "[说明](my%20notes.txt?download=1#details)",
                ),
            ):
                (bundle / f"index.{language}.md").write_text(
                    f'''+++
title = "{title}"
date = 2026-08-09
draft = false
interactionId = "resource-suffixes"
+++

{body}
''',
                    encoding="utf-8",
                )
            svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>'
            (bundle / "my diagram.svg").write_text(
                svg,
                encoding="utf-8",
            )
            (bundle / "diagram.svg").write_text(
                svg,
                encoding="utf-8",
            )
            (bundle / "my notes.txt").write_text(
                "Fixture notes.\n",
                encoding="utf-8",
            )

            for name, base_url, base_path in (
                ("root", "https://example.test/", "/"),
                (
                    "project",
                    "https://example.test/example-blog/",
                    "/example-blog/",
                ),
            ):
                public = temporary_root / name / "public"
                build_site(
                    public,
                    base_url,
                    "--contentDir",
                    str(content),
                )
                expected_image = (
                    f'{base_path}p/resource-suffixes/my%20diagram.svg'
                    "?mode=print#preview"
                )
                expected_minipic = (
                    f'{base_path}p/resource-suffixes/diagram.svg#minipic'
                )
                expected_link = (
                    f'{base_path}p/resource-suffixes/my%20notes.txt'
                    "?download=1#details"
                )
                for language_path in ("", "zh/"):
                    html = read_html(
                        public,
                        f"{language_path}p/resource-suffixes/index.html",
                    )
                    with self.subTest(build=name, language=language_path or "en"):
                        self.assertIn(f'src="{expected_image}"', html)
                        self.assertIn(f'src="{expected_minipic}"', html)
                        self.assertIn(f'href="{expected_link}"', html)
                self.assertTrue(
                    (public / "p/resource-suffixes/my diagram.svg").is_file()
                )
                self.assertTrue(
                    (public / "p/resource-suffixes/diagram.svg").is_file()
                )
                self.assertTrue(
                    (public / "p/resource-suffixes/my notes.txt").is_file()
                )

    def test_localized_brand_contact_and_generated_favicons(self):
        source = ROOT / "assets/images/drawing-hands.png"
        self.assertTrue(source.is_file())

        expected_favicon_keys = {
            ("icon", "32x32"),
            ("apple-touch-icon", "180x180"),
        }
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            for name, base_url, base_path in (
                ("root", "https://example.test/", "/"),
                (
                    "project",
                    "https://example.test/example-blog/",
                    "/example-blog/",
                ),
            ):
                public = temporary_root / name / "public"
                build_site(public, base_url, "--config", BRANDING_CONFIG)
                english = read_html(public, "index.html")
                chinese = read_html(public, "zh/index.html")

                self.assertIn(f"<title>{FIXTURE_TITLE_EN}</title>", english)
                self.assertIn(f"<h1>{FIXTURE_TITLE_EN}</h1>", english)
                self.assertIn(f"<title>{FIXTURE_TITLE_ZH}</title>", chinese)
                self.assertIn(f"<h1>{FIXTURE_TITLE_ZH}</h1>", chinese)

                favicon_links: dict[str, dict[tuple[str, str], str]] = {}
                for language, html in (("en", english), ("zh", chinese)):
                    with self.subTest(build=name, language=language):
                        self.assertNotRegex(
                            html,
                            rf">[^<]*{re.escape(FIXTURE_CONTACT_EMAIL)}[^<]*<",
                        )
                        png_link_tags = [
                            tag
                            for tag in re.findall(r"<link\b[^>]*>", html)
                            if 'type="image/png"' in tag
                        ]
                        self.assertEqual(2, len(png_link_tags))

                        entries: dict[tuple[str, str], str] = {}
                        for tag in png_link_tags:
                            attributes = dict(
                                re.findall(r'([:\w-]+)="([^"]*)"', tag)
                            )
                            key = (attributes.get("rel"), attributes.get("sizes"))
                            href = attributes.get("href")
                            self.assertIsNotNone(href)
                            entries[key] = href

                        self.assertEqual(expected_favicon_keys, set(entries))
                        for (_, sizes), href in entries.items():
                            parsed = urlsplit(href)
                            self.assertEqual("", parsed.scheme)
                            self.assertEqual("", parsed.netloc)
                            self.assertTrue(parsed.path.startswith(base_path), href)
                            relative_asset = parsed.path.removeprefix(base_path)
                            self.assertNotIn("..", Path(relative_asset).parts)
                            generated_asset = public / relative_asset
                            self.assertTrue(generated_asset.is_file(), generated_asset)
                            expected_dimensions = tuple(
                                int(value) for value in sizes.split("x")
                            )
                            self.assertEqual(
                                expected_dimensions,
                                png_dimensions(generated_asset),
                            )

                        favicon_links[language] = entries

                self.assertEqual(favicon_links["en"], favicon_links["zh"])

    def test_home_sections_are_ordered_title_only_and_language_local(self):
        with TemporaryDirectory() as temporary:
            for name, base_url in (
                ("root", "https://example.test/"),
                ("project", "https://example.test/example-blog/"),
            ):
                public = Path(temporary) / name
                build_site(
                    public,
                    base_url,
                    "--config",
                    "hugo.toml,tests/fixtures/interactions.toml",
                    "--contentDir",
                    "tests/fixtures/content",
                )
                pages = {
                    "en": read_html(public, "index.html"),
                    "zh": read_html(public, "zh/index.html"),
                }
                labels = {
                    "en": ("Projects", "Latest posts", "Popular posts"),
                    "zh": ("项目", "最新文章", "热门文章"),
                }
                for language, html in pages.items():
                    with self.subTest(build=name, language=language):
                        self.assertLess(
                            html.index('class="home-intro"'),
                            html.index('data-home-section="projects"'),
                        )
                        self.assertLess(
                            html.index('data-home-section="projects"'),
                            html.index('data-home-section="latest"'),
                        )
                        self.assertLess(
                            html.index('data-home-section="latest"'),
                            html.index('data-home-section="popular"'),
                        )
                        for heading in labels[language]:
                            self.assertIn(f"<h2>{heading}</h2>", html)

                english = pages["en"]
                self.assertIn("Shared project", english)
                self.assertIn("Older project", english)
                self.assertNotIn("共享项目", english)
                english_latest = re.search(
                    r'<section data-home-section="latest">(.*?)</section>',
                    english,
                    re.DOTALL,
                ).group(1)
                self.assertIn("Shared article", english_latest)
                self.assertNotIn("共享文章", english_latest)
                self.assertNotRegex(english_latest, r"<time|data-post-count|#[\w-]+")
                self.assertEqual(1, english_latest.count("<li>"))

                chinese = pages["zh"]
                self.assertIn("共享项目", chinese)
                self.assertNotIn("Older project", chinese)
                chinese_latest = re.search(
                    r'<section data-home-section="latest">(.*?)</section>',
                    chinese,
                    re.DOTALL,
                ).group(1)
                self.assertIn("共享文章", chinese_latest)
                self.assertIn("仅中文文章", chinese_latest)
                self.assertNotIn("Shared article", chinese_latest)
                self.assertNotRegex(chinese_latest, r"<time|data-post-count|#[\w-]+")
                self.assertEqual(2, chinese_latest.count("<li>"))

    def test_escaping_thought_is_localized_home_only_and_base_path_safe(self):
        module_pattern = re.compile(
            r'<script(?=[^>]*\btype="module")'
            r'(?=[^>]*\bsrc="([^"]*home-ending[^"]*)")'
            r'(?=[^>]*\bintegrity="([^"]+)")[^>]*></script>'
        )
        expected = {
            "en": (
                "There was one more thing...",
                "↑ perhaps start over",
            ),
            "zh": (
                "好像还有件事……",
                "↑ 要不从头再来",
            ),
        }

        with TemporaryDirectory() as temporary:
            for name, base_url, base_path in (
                ("root", "https://example.test/", "/"),
                ("project", "https://example.test/example-blog/", "/example-blog/"),
            ):
                public = Path(temporary) / name
                build_site(
                    public,
                    base_url,
                    "--config",
                    "hugo.toml,tests/fixtures/interactions.toml",
                    "--contentDir",
                    "tests/fixtures/content",
                )
                pages = {
                    "en": read_html(public, "index.html"),
                    "zh": read_html(public, "zh/index.html"),
                }

                for language, html in pages.items():
                    with self.subTest(build=name, language=language):
                        thought, return_label = expected[language]
                        self.assertEqual(
                            1,
                            len(re.findall(
                                r'<div\b[^>]*\sdata-home-ending(?:\s|>)',
                                html,
                            )),
                        )
                        self.assertIn('id="home-top"', html)
                        self.assertIn('data-home-ending-state="static"', html)
                        self.assertIn(f'aria-label="{thought}"', html)
                        self.assertIn(f'href="#home-top">{return_label}</a>', html)
                        ending = html[
                            html.index('<div class="home-ending"'):
                            html.index("<footer>")
                        ]
                        self.assertEqual(1, ending.count("data-home-ending-balloon"))
                        self.assertNotIn("data-home-ending-dot", ending)
                        self.assertRegex(
                            ending,
                            r'<svg\b(?=[^>]*\bdata-home-ending-balloon(?:\s|>))'
                            r'(?=[^>]*\bviewBox="0 0 64 48")'
                            r'(?=[^>]*\bwidth="36")'
                            r'(?=[^>]*\bheight="27")'
                            r'(?=[^>]*\baria-hidden="true")'
                            r'(?=[^>]*\bfocusable="false")[^>]*>',
                        )
                        self.assertEqual(1, ending.count("<path "))
                        self.assertEqual(2, ending.count("<circle "))
                        self.assertLess(
                            html.index('data-home-section="popular"'),
                            html.index("data-home-ending"),
                        )
                        self.assertLess(
                            html.index("data-home-ending"),
                            html.index("<footer>"),
                        )
                        self.assertNotRegex(
                            html[html.index("data-home-ending"):html.index("<footer>")],
                            r"<(?:img|picture|video)\b",
                        )

                        modules = module_pattern.findall(html)
                        self.assertEqual(1, len(modules))
                        source, integrity = modules[0]
                        self.assertRegex(
                            source,
                            rf"^{re.escape(base_path)}js/"
                            r"home-ending\.[0-9a-f]{64}\.mjs$",
                        )
                        asset = public / urlsplit(source).path.removeprefix(base_path)
                        self.assertTrue(asset.is_file(), source)
                        expected_integrity = "sha256-" + base64.b64encode(
                            hashlib.sha256(asset.read_bytes()).digest()
                        ).decode("ascii")
                        self.assertEqual(expected_integrity, unescape(integrity))

                for relative in (
                    "p/shared-article/index.html",
                    "zh/p/shared-article/index.html",
                    "blog/index.html",
                    "zh/blog/index.html",
                    "tags/index.html",
                    "zh/tags/index.html",
                    "404.html",
                ):
                    with self.subTest(build=name, non_home=relative):
                        self.assertNotIn(
                            "data-home-ending",
                            read_html(public, relative),
                        )

    def test_home_latest_is_capped_at_three_visible_posts(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            content.mkdir()
            (content / "_index.en.md").write_text(
                '+++\ntitle = "Fixture Home"\n+++\n\nFixture home.\n',
                encoding="utf-8",
            )
            (content / "_index.zh.md").write_text(
                '+++\ntitle = "测试首页"\n+++\n\n测试首页。\n',
                encoding="utf-8",
            )
            for ordinal in range(1, 5):
                bundle = content / "blog" / f"post-{ordinal}"
                bundle.mkdir(parents=True)
                (bundle / "index.en.md").write_text(
                    "+++\n"
                    f'title = "Post {ordinal}"\n'
                    f"date = 2026-01-0{ordinal}\n"
                    "draft = false\n"
                    f'interactionId = "post-{ordinal}"\n'
                    "+++\n\nBody.\n",
                    encoding="utf-8",
                )
            hidden = content / "blog/hidden-post"
            hidden.mkdir(parents=True)
            (hidden / "index.en.md").write_text(
                '+++\ntitle = "Hidden post"\ndate = 2026-01-05\n'
                'draft = false\nhidden = true\ninteractionId = "hidden-post"\n'
                '+++\n\nHidden.\n',
                encoding="utf-8",
            )
            draft_post = content / "blog/draft-post"
            draft_post.mkdir(parents=True)
            (draft_post / "index.en.md").write_text(
                '+++\ntitle = "Draft post"\ndate = 2026-01-06\n'
                'draft = true\ninteractionId = "draft-post"\n'
                '+++\n\nDraft.\n',
                encoding="utf-8",
            )
            draft_project = content / "projects/draft-project"
            draft_project.mkdir(parents=True)
            (draft_project / "index.en.md").write_text(
                '+++\ntitle = "Draft project"\ndate = 2026-01-06\n'
                'draft = true\ninteractionId = "draft-project"\n'
                'projectStatus = "past"\n+++\n\nDraft project.\n',
                encoding="utf-8",
            )

            for name, base_url, base_path in (
                ("root", "https://example.test/", "/"),
                (
                    "project",
                    "https://example.test/example-blog/",
                    "/example-blog/",
                ),
            ):
                public = temporary_root / name
                build_site(
                    public,
                    base_url,
                    "--contentDir",
                    str(content),
                    "--buildDrafts",
                )
                home = read_html(public, "index.html")
                latest_match = re.search(
                    r'<section data-home-section="latest">(.*?)</section>',
                    home,
                    re.DOTALL,
                )
                with self.subTest(build=name):
                    self.assertIsNotNone(latest_match)
                    latest = latest_match.group(1)
                    self.assertEqual(
                        ["Post 4", "Post 3", "Post 2"],
                        re.findall(r"<a[^>]*>([^<]+)</a>", latest),
                    )
                    self.assertIn(f'href="{base_path}p/post-4/"', latest)
                    self.assertNotIn("Post 1", latest)
                    self.assertNotIn("Hidden post", latest)
                    self.assertNotIn("Draft post", latest)
                    self.assertNotIn("Draft project", home)


    def test_popular_candidates_exclude_hidden_posts_in_each_language(self):
        candidate_pattern = re.compile(
            r'<li\b(?=[^>]*\bdata-popular-candidate(?:\s|>))'
            r'(?=[^>]*\bdata-entity="([^"]+)")'
            r'(?=[^>]*\bdata-recency="(\d+)")[^>]*>'
            r'\s*<a\b[^>]*href="([^"]+)"[^>]*>([^<]+)</a>\s*</li>'
        )
        module_pattern = re.compile(
            r'<script(?=[^>]*\btype="module")'
            r'(?=[^>]*\bsrc="([^"]*popular-posts[^"]*)")'
            r'(?=[^>]*\bintegrity="([^"]+)")[^>]*></script>'
        )

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            content.mkdir()
            (content / "_index.en.md").write_text(
                '+++\ntitle = "Fixture Home"\n+++\n\nFixture home.\n',
                encoding="utf-8",
            )
            (content / "_index.zh.md").write_text(
                '+++\ntitle = "测试首页"\n+++\n\n测试首页。\n',
                encoding="utf-8",
            )
            pages = (
                (
                    "visible-1",
                    "2026-01-01",
                    False,
                    False,
                    "Visible one",
                    "可见文章一",
                ),
                (
                    "visible-2",
                    "2026-01-02",
                    False,
                    False,
                    "Visible two",
                    "可见文章二",
                ),
                (
                    "hidden-post",
                    "2026-01-03",
                    False,
                    True,
                    "Hidden post",
                    "隐藏文章",
                ),
                (
                    "draft-post",
                    "2026-01-04",
                    True,
                    False,
                    "Draft post",
                    "草稿文章",
                ),
            )
            for slug, date, draft, hidden, english_title, chinese_title in pages:
                bundle = content / "blog" / slug
                bundle.mkdir(parents=True)
                for language, title in (
                    ("en", english_title),
                    ("zh", chinese_title),
                ):
                    (bundle / f"index.{language}.md").write_text(
                        "+++\n"
                        f'title = "{title}"\n'
                        f"date = {date}\n"
                        f"draft = {str(draft).lower()}\n"
                        f"hidden = {str(hidden).lower()}\n"
                        f'interactionId = "{slug}"\n'
                        "+++\n\nBody.\n",
                        encoding="utf-8",
                    )

            for name, base_url, base_path in (
                ("root", "https://example.test/", "/"),
                (
                    "project",
                    "https://example.test/example-blog/",
                    "/example-blog/",
                ),
            ):
                public = temporary_root / name
                build_site(
                    public,
                    base_url,
                    "--contentDir",
                    str(content),
                    "--buildDrafts",
                )
                for language, relative, language_path, titles, noscript in (
                    (
                        "en",
                        "index.html",
                        "",
                        ("Visible two", "Visible one"),
                        "Enable JavaScript to load popular posts",
                    ),
                    (
                        "zh",
                        "zh/index.html",
                        "zh/",
                        ("可见文章二", "可见文章一"),
                        "请启用 JavaScript 以加载热门文章",
                    ),
                ):
                    html = read_html(public, relative)
                    match = re.search(
                        r'<section data-home-section="popular">'
                        r'(.*?)</section>',
                        html,
                        re.DOTALL,
                    )
                    self.assertIsNotNone(match)
                    popular = match.group(1)
                    with self.subTest(build=name, language=language):
                        self.assertEqual(
                            [
                                (
                                    "post:visible-2",
                                    "0",
                                    f"{base_path}{language_path}p/visible-2/",
                                    titles[0],
                                ),
                                (
                                    "post:visible-1",
                                    "1",
                                    f"{base_path}{language_path}p/visible-1/",
                                    titles[1],
                                ),
                            ],
                            candidate_pattern.findall(popular),
                        )
                        self.assertNotIn("hidden-post", popular)
                        self.assertNotIn("draft-post", popular)
                        self.assertNotIn("Hidden post", popular)
                        self.assertNotIn("Draft post", popular)
                        self.assertNotIn("隐藏文章", popular)
                        self.assertNotIn("草稿文章", popular)
                        self.assertEqual(1, popular.count('role="status"'))
                        modules = module_pattern.findall(popular)
                        self.assertEqual(1, len(modules))
                        source, integrity = modules[0]
                        self.assertRegex(
                            source,
                            rf'^{re.escape(base_path)}js/'
                            r'popular-posts\.[0-9a-f]{64}\.mjs$',
                        )
                        source_path = urlsplit(source).path
                        self.assertTrue(source_path.startswith(base_path), source)
                        asset = public / source_path.removeprefix(base_path)
                        self.assertTrue(asset.is_file(), source)
                        expected_integrity = "sha256-" + base64.b64encode(
                            hashlib.sha256(asset.read_bytes()).digest()
                        ).decode("ascii")
                        self.assertEqual(expected_integrity, unescape(integrity))
                        self.assertRegex(
                            popular,
                            r'</div>\s*<noscript><p class="home-empty">'
                            + re.escape(noscript)
                            + r'</p></noscript>',
                        )

    def test_popular_posts_do_not_load_ranking_for_zero_or_one_candidate(self):
        module_pattern = re.compile(
            r'<script(?=[^>]*\btype="module")'
            r'(?=[^>]*\bsrc="[^"]*popular-posts[^"]*")'
            r'(?=[^>]*\bintegrity="[^"]+")[^>]*></script>'
        )

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            content.mkdir()
            (content / "_index.en.md").write_text(
                '+++\ntitle = "Fixture Home"\n+++\n\nFixture home.\n',
                encoding="utf-8",
            )
            (content / "_index.zh.md").write_text(
                '+++\ntitle = "测试首页"\n+++\n\n测试首页。\n',
                encoding="utf-8",
            )
            bundle = content / "blog" / "only-post"
            bundle.mkdir(parents=True)
            (bundle / "index.en.md").write_text(
                '+++\ntitle = "Only post"\ndate = 2026-01-01\n'
                'draft = false\ninteractionId = "only-post"\n'
                '+++\n\nBody.\n',
                encoding="utf-8",
            )

            for name, base_url, base_path in (
                ("root", "https://example.test/", "/"),
                (
                    "project",
                    "https://example.test/example-blog/",
                    "/example-blog/",
                ),
            ):
                public = temporary_root / name
                build_site(
                    public,
                    base_url,
                    "--contentDir",
                    str(content),
                )
                english = read_html(public, "index.html")
                chinese = read_html(public, "zh/index.html")
                english_match = re.search(
                    r'<section data-home-section="popular">'
                    r'(.*?)</section>',
                    english,
                    re.DOTALL,
                )
                chinese_match = re.search(
                    r'<section data-home-section="popular">'
                    r'(.*?)</section>',
                    chinese,
                    re.DOTALL,
                )
                self.assertIsNotNone(english_match)
                self.assertIsNotNone(chinese_match)

                with self.subTest(build=name, language="en"):
                    popular = english_match.group(1)
                    self.assertIn("Only post", popular)
                    self.assertIn(
                        f'href="{base_path}p/only-post/"',
                        popular,
                    )
                    self.assertNotIn("data-popular-posts", popular)
                    self.assertNotIn("data-popular-candidate", popular)
                    self.assertEqual([], module_pattern.findall(popular))

                with self.subTest(build=name, language="zh"):
                    popular = chinese_match.group(1)
                    self.assertIn("暂无文章", popular)
                    self.assertNotIn("Only post", popular)
                    self.assertNotIn("data-popular-posts", popular)
                    self.assertNotIn("data-popular-candidate", popular)
                    self.assertEqual([], module_pattern.findall(popular))

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

    def test_chrome_is_localized_configurable_and_uses_browser_color_preference(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/", "--config", BRANDING_CONFIG)
            english = read_html(public, "index.html")
            chinese = read_html(public, "zh/index.html")

            self.assertIn(f"<title>{FIXTURE_TITLE_EN}</title>", english)
            self.assertIn(f"<title>{FIXTURE_TITLE_ZH}</title>", chinese)
            self.assertEqual(
                [("/", "Home"), ("/blog/", "Blog"), ("/tags/", "Tags")],
                primary_navigation(english),
            )
            self.assertEqual(
                [("/zh/", "首页"), ("/zh/blog/", "博客"), ("/zh/tags/", "标签")],
                primary_navigation(chinese),
            )
            self.assertIn('<html lang="en-US"', english)
            self.assertIn('<html lang="zh-CN"', chinese)
            for html in (english, chinese):
                self.assertIn('name="color-scheme" content="light dark"', html)
                self.assertIn(
                    'name="referrer" content="strict-origin-when-cross-origin"',
                    html,
                )
                self.assertIn('media="(prefers-color-scheme: light)"', html)
                self.assertIn('media="(prefers-color-scheme: dark)"', html)
                self.assertNotIn("theme-toggle", html)

            for language, html, alternate_label in (
                ("en", english, "中文"),
                ("zh", chinese, "English"),
            ):
                with self.subTest(language=language):
                    self.assertEqual(
                        [
                            [
                                ("nav", True, ()),
                                ("nav", False, ("language-switcher",)),
                            ]
                        ],
                        header_navigation_signatures(html),
                    )
                    self.assertIn(f">{alternate_label}</a>", html)

            for language, html, rss_path, contact_label, scholar_label in (
                ("en", english, "/index.xml", "Contact", "Google Scholar"),
                ("zh", chinese, "/zh/index.xml", "联系", "谷歌学术"),
            ):
                footer = re.search(r"<footer>(.*?)</footer>", html, re.DOTALL)
                self.assertIsNotNone(footer)
                with self.subTest(language=language):
                    markup = footer.group(1)
                    self.assertEqual(
                        [
                            f"mailto:{FIXTURE_CONTACT_EMAIL}",
                            FIXTURE_GITHUB_URL,
                            FIXTURE_SCHOLAR_URL,
                            rss_path,
                        ],
                        re.findall(r'<a\b[^>]*\bhref="([^"]+)"', markup),
                    )
                    self.assertIn(f'aria-label="{contact_label}"', markup)
                    self.assertIn('alt="GitHub"', markup)
                    self.assertIn(f'alt="{scholar_label}"', markup)
                    self.assertNotRegex(
                        markup,
                        rf">[^<]*{re.escape(FIXTURE_CONTACT_EMAIL)}[^<]*<",
                    )

    def test_semantic_colors_meet_text_contrast_in_both_color_schemes(self):
        site_css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
        site_base = css_root_custom_properties(site_css)
        site_light = css_root_custom_properties(site_css, scheme="light")
        for token in ("--text-color-tertiary", "--upvoted-color"):
            self.assertIn(token, site_light)
            self.assertNotIn(token, site_base)

        for scheme, properties in semantic_color_tokens().items():
            for token in ("--text-color-tertiary", "--upvoted-color"):
                with self.subTest(scheme=scheme, token=token):
                    ratio = wcag_contrast_ratio(
                        properties[token],
                        properties["--bg-color-primary"],
                    )
                    self.assertGreaterEqual(ratio, 4.5)

    def test_home_ending_has_large_gap_thought_balloon_and_reduced_fallback(self):
        css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")

        self.assertRegex(
            css,
            r"\.home-ending\s*\{[^}]*"
            r"margin-block-start:\s*clamp\(8rem,\s*25vh,\s*15rem\);",
        )
        for name in ("home-ending-balloon", "home-ending-return"):
            self.assertEqual(1, css.count(f"@keyframes {name}"))
        for removed_name in (
            "home-ending-dot-one",
            "home-ending-dot-two",
            "home-ending-dot-three",
        ):
            self.assertNotIn(removed_name, css)
        self.assertRegex(
            css,
            r"\.home-ending-balloon\s*\{[^}]*"
            r"color:\s*var\(--text-color-secondary\);[^}]*"
            r"height:\s*1\.7em;[^}]*"
            r"width:\s*2\.25em;",
        )
        self.assertIn("animation-iteration-count: 1", css)
        reduced = re.search(
            r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([\s\S]*)\}\s*$",
            css,
        )
        self.assertIsNotNone(reduced)
        self.assertIn("animation: none", reduced.group(1))
        self.assertIn("visibility: visible", reduced.group(1))

    def test_highlighted_code_follows_the_reader_color_scheme(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(
                public,
                "https://example.test/",
                "--contentDir",
                "tests/fixtures/content",
            )
            article = read_html(public, "p/shared-article/index.html")
            stylesheets = [
                (public / urlsplit(href).path.lstrip("/")).read_text(
                    encoding="utf-8"
                )
                for href in re.findall(
                    r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"',
                    article,
                )
            ]

        highlighted = re.search(
            r'<div class="highlight">(.*?)</div>',
            article,
            re.DOTALL,
        )
        self.assertIsNotNone(highlighted)
        block = highlighted.group(1)
        self.assertIn('class="chroma"', block)
        # Inline colors cannot answer prefers-color-scheme, so highlighting has
        # to come from a stylesheet the page actually loads.
        self.assertNotRegex(block, r"(?<![-\w])color:\s*#")
        syntax = [css for css in stylesheets if ".chroma" in css]
        self.assertEqual(1, len(syntax))

        tokens = semantic_color_tokens()
        for scheme in ("light", "dark"):
            rules = chroma_rules(syntax[0], scheme)
            self.assertTrue(rules, scheme)
            background = tokens[scheme]["--bg-color-secondary"]
            with self.subTest(scheme=scheme, token="block"):
                self.assertEqual("var(--bg-color-secondary)", rules[""][1])
                self.assertGreaterEqual(
                    wcag_contrast_ratio(
                        rules[""][0] or tokens[scheme]["--text-color-primary"],
                        background,
                    ),
                    4.5,
                )
            for name, (color, own_background) in rules.items():
                if not name or name in CHROMA_NON_TEXT_CLASSES or color is None:
                    continue
                with self.subTest(scheme=scheme, token=name):
                    self.assertGreaterEqual(
                        wcag_contrast_ratio(color, own_background or background),
                        4.5,
                    )

    def test_callouts_fold_on_the_author_marker_and_localize_their_label(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(
                public,
                "https://example.test/",
                "--contentDir",
                "tests/fixtures/content",
            )
            english = read_html(public, "p/shared-article/index.html")
            chinese = read_html(public, "zh/p/shared-article/index.html")

        folded, unfolded = re.findall(
            r"<details\b([^>]*)>(.*?)</details>",
            english,
            re.DOTALL,
        )
        with self.subTest(marker="-"):
            self.assertNotIn("open", folded[0])
            self.assertIn("<summary>Folded fixture callout</summary>", folded[1])
            # The body is markdown, not raw text: its code block still highlights.
            self.assertIn('class="chroma"', folded[1])
        with self.subTest(marker="+"):
            self.assertIn("open", unfolded[0])
            self.assertIn("<summary>Unfolded fixture callout</summary>", unfolded[1])

        # An unmarked callout stays open prose, and plain quotes stay blockquotes.
        self.assertNotIn("Fixture warning body", folded[1] + unfolded[1])
        self.assertRegex(english, r">Warning</[a-z]+>\s*<p>Fixture warning body")
        self.assertRegex(chinese, r">警告</[a-z]+>\s*<p>测试警告内容")
        self.assertIn("<blockquote>", english)
        self.assertRegex(english, r"<blockquote>\s*<p>Plain fixture quote")

    def test_istanbul_working_session_is_folded_by_default(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            page = read_html(public, "p/the-miracle-of-istanbul/index.html")

        callout = re.search(
            r'<details class="callout callout-note"([^>]*)>(.*?)</details>',
            page,
            re.DOTALL,
        )
        self.assertIsNotNone(callout)
        self.assertNotIn("open", callout.group(1))
        self.assertIn("<summary>My working session</summary>", callout.group(2))
        callout_text = unescape(re.sub(r"<[^>]+>", "", callout.group(2)))
        self.assertIn("sessionInfo()", callout_text)
        self.assertIn("R version 4.1.0", callout_text)

    def test_upvoted_icon_adds_a_non_color_pressed_cue(self):
        kudos = (ROOT / "layouts/_partials/kudos.html").read_text(
            encoding="utf-8"
        )
        css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
        self.assertIn('fill="none"', kudos)
        self.assertRegex(
            css,
            r"button\.upvoted\s+svg\s*\{[^}]*fill:\s*currentColor;[^}]*\}",
        )

    def test_popular_posts_keep_order_but_render_bullets(self):
        partial = (ROOT / "layouts/_partials/popular-posts.html").read_text(
            encoding="utf-8"
        )
        css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
        self.assertIn('<ol class="home-title-list" data-popular-list', partial)
        self.assertRegex(
            css,
            r"ol\.home-title-list\s*\{[^}]*list-style-type:\s*disc;[^}]*\}",
        )

    def test_initial_chinese_lists_are_valid_and_empty(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            blog = content / "blog"
            blog.mkdir(parents=True)
            (blog / "_index.en.md").write_text(
                '+++\ntitle = "Blog"\n+++\n',
                encoding="utf-8",
            )
            (blog / "_index.zh.md").write_text(
                '+++\ntitle = "博客"\n+++\n',
                encoding="utf-8",
            )
            public = temporary_root / "public"
            build_site(
                public,
                "https://example.test/",
                "--contentDir",
                str(content),
            )
            posts = read_html(public, "zh/blog/index.html")
            tags = read_html(public, "zh/tags/index.html")
            self.assertIn("暂无文章", posts)
            self.assertIn("暂无标签", tags)
            self.assertNotIn("No posts yet", posts)
            self.assertNotIn("No tags yet", tags)

    def test_post_search_has_localized_no_match_feedback(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(
                public,
                "https://example.test/",
                "--config",
                "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir",
                "tests/fixtures/content",
            )
            english = read_html(public, "blog/index.html")
            self.assertIn('data-search-empty', english)
            self.assertIn("No matching posts", english)

    def test_tag_results_group_projects_before_posts(self):
        with TemporaryDirectory() as temporary:
            for name, base_url, base_path in (
                ("root", "https://example.test/", "/"),
                (
                    "project",
                    "https://example.test/example-blog/",
                    "/example-blog/",
                ),
            ):
                public = Path(temporary) / name
                build_site(
                    public,
                    base_url,
                    "--config",
                    "hugo.toml,tests/fixtures/interactions.toml",
                    "--contentDir",
                    "tests/fixtures/content",
                )
                english = read_html(public, "tags/fixture/index.html")
                chinese = read_html(public, "zh/tags/测试/index.html")
                english_home = read_html(public, "index.html")
                chinese_home = read_html(public, "zh/index.html")
                self.assertIn("<h2>Tag: fixture</h2>", english)
                self.assertIn("<h2>标签：测试</h2>", chinese)
                self.assertNotIn(">All tags</a>", english)
                self.assertNotIn(">全部标签</a>", chinese)
                self.assertIn("Shared project", english_home)
                self.assertIn("Older project", english_home)
                self.assertIn("共享项目", chinese_home)
                self.assertNotIn("共享项目", english_home)
                self.assertNotIn("Shared project", chinese_home)
                self.assertNotIn("Older project", chinese_home)
                self.assertIn(">Projects</h3>", english)
                self.assertIn(">Blog</h3>", english)
                self.assertLess(
                    english.index(">Projects</h3>"),
                    english.index(">Blog</h3>"),
                )
                self.assertLess(
                    english.index("Shared project"),
                    english.index("Shared article"),
                )
                self.assertIn(">项目</h3>", chinese)
                self.assertIn(">博客</h3>", chinese)
                self.assertLess(
                    chinese.index(">项目</h3>"),
                    chinese.index(">博客</h3>"),
                )
                self.assertLess(
                    chinese.index("共享项目"),
                    chinese.index("共享文章"),
                )

                english_projects = re.search(
                    r'<section data-tag-group="projects">(.*?)</section>',
                    english,
                    re.DOTALL,
                ).group(1)
                english_posts = re.search(
                    r'<section data-tag-group="posts">(.*?)</section>',
                    english,
                    re.DOTALL,
                ).group(1)
                chinese_projects = re.search(
                    r'<section data-tag-group="projects">(.*?)</section>',
                    chinese,
                    re.DOTALL,
                ).group(1)
                chinese_posts = re.search(
                    r'<section data-tag-group="posts">(.*?)</section>',
                    chinese,
                    re.DOTALL,
                ).group(1)

                for group in (
                    english_projects,
                    english_posts,
                    chinese_projects,
                    chinese_posts,
                ):
                    self.assertNotIn("data-post-count", group)

                self.assertIn("Shared project", english_projects)
                self.assertIn("Older project", english_projects)
                self.assertNotIn("Shared article", english_projects)
                self.assertIn(
                    'placeholder="Search projects"',
                    english_projects,
                )
                self.assertIn("No matching projects", english_projects)
                self.assertEqual(1, english_projects.count("data-post-search"))
                self.assertIn("Shared article", english_posts)
                self.assertNotIn("Shared project", english_posts)
                self.assertNotIn("Older project", english_posts)
                self.assertEqual(0, english_posts.count("data-post-search"))
                self.assertIn("共享项目", chinese_projects)
                self.assertNotIn("共享文章", chinese_projects)
                self.assertEqual(0, chinese_projects.count("data-post-search"))
                self.assertIn("共享文章", chinese_posts)
                self.assertIn("仅中文文章", chinese_posts)
                self.assertNotIn("共享项目", chinese_posts)
                self.assertIn('placeholder="搜索..."', chinese_posts)
                self.assertEqual(1, chinese_posts.count("data-post-search"))
                self.assertEqual(1, english.count("js/post-search."))
                self.assertEqual(1, chinese.count("js/post-search."))

                for path in (
                    "p/shared-project/",
                    "p/older-project/",
                    "p/shared-article/",
                ):
                    self.assertIn(f'href="{base_path}{path}"', english)
                self.assertIn(
                    f'href="{base_path}zh/p/shared-project/"',
                    chinese,
                )
                self.assertIn(
                    f'href="{base_path}zh/p/shared-article/"',
                    chinese,
                )
                overview = read_html(public, "tags/index.html")
                chinese_overview = read_html(public, "zh/tags/index.html")
                self.assertRegex(
                    overview,
                    r"#fixture</a><span[^>]*>3</span>",
                )
                self.assertRegex(
                    chinese_overview,
                    r"#测试</a><span[^>]*>3</span>",
                )

                english_sitemap = ET.parse(
                    public / "en/sitemap.xml"
                ).getroot()
                chinese_sitemap = ET.parse(
                    public / "zh/sitemap.xml"
                ).getroot()
                english_locations = [
                    node.findtext("{*}loc")
                    for node in english_sitemap.findall("{*}url")
                ]
                chinese_locations = [
                    node.findtext("{*}loc")
                    for node in chinese_sitemap.findall("{*}url")
                ]
                self.assertTrue(all(english_locations))
                self.assertTrue(all(chinese_locations))
                self.assertNotIn(
                    f"{base_url}projects/",
                    english_locations,
                )
                self.assertNotIn(
                    f"{base_url}zh/projects/",
                    chinese_locations,
                )
                self.assertIn(
                    f"{base_url}p/shared-project/",
                    english_locations,
                )
                self.assertIn(
                    f"{base_url}p/older-project/",
                    english_locations,
                )
                self.assertNotIn(
                    f"{base_url}zh/p/shared-project/",
                    english_locations,
                )
                self.assertIn(
                    f"{base_url}zh/p/shared-project/",
                    chinese_locations,
                )
                self.assertNotIn(
                    f"{base_url}p/shared-project/",
                    chinese_locations,
                )
                self.assertNotIn(
                    f"{base_url}p/older-project/",
                    chinese_locations,
                )
                self.assertNotIn(
                    f"{base_url}zh/p/older-project/",
                    chinese_locations,
                )

                english_blog = read_html(public, "blog/index.html")
                self.assertNotIn("data-post-count", english_blog)
                self.assertEqual(1, english_blog.count("data-post-search"))
                self.assertEqual(1, english_blog.count("js/post-search."))

    def test_searchable_tag_groups_share_one_module(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            shutil.copytree(ROOT / "tests/fixtures/content", content)

            second_article = content / "blog/second-article"
            second_article.mkdir()
            (second_article / "index.en.md").write_text(
                """+++
title = "Second article"
date = 2026-08-06
lastmod = 2026-08-06
draft = false
tags = ["fixture"]
interactionId = "second-article"
+++

Second English article.
""",
                encoding="utf-8",
            )
            second_project = content / "projects/second-project"
            second_project.mkdir()
            (second_project / "index.zh.md").write_text(
                """+++
title = "第二个项目"
date = 2026-08-06
lastmod = 2026-08-06
draft = false
tags = ["测试"]
interactionId = "second-project"
projectStatus = "past"
+++

第二个中文项目。
""",
                encoding="utf-8",
            )

            public = temporary_root / "public"
            build_site(
                public,
                "https://example.test/",
                "--config",
                "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir",
                str(content),
            )
            english = read_html(public, "tags/fixture/index.html")
            chinese = read_html(public, "zh/tags/测试/index.html")
            module_pattern = re.compile(
                r'<script type="module" src="/js/post-search\.[^"]+\.mjs" '
                r'integrity="sha256-[^"]+"></script>'
            )

            for language, html, groups in (
                (
                    "en",
                    english,
                    (
                        (
                            "projects",
                            "{count} project",
                            "{count} projects",
                            "Search projects",
                            "No matching projects",
                        ),
                        (
                            "posts",
                            "{count} post",
                            "{count} posts",
                            "Search...",
                            "No matching posts",
                        ),
                    ),
                ),
                (
                    "zh",
                    chinese,
                    (
                        (
                            "projects",
                            "{count} 个项目",
                            "{count} 个项目",
                            "搜索项目",
                            "没有匹配的项目",
                        ),
                        (
                            "posts",
                            "{count} 篇文章",
                            "{count} 篇文章",
                            "搜索...",
                            "没有匹配的文章",
                        ),
                    ),
                ),
            ):
                with self.subTest(language=language, contract="shared module"):
                    self.assertEqual(2, html.count("data-post-search"))
                    self.assertEqual(1, len(module_pattern.findall(html)))

                for (
                    group_name,
                    count_one,
                    count_many,
                    placeholder,
                    no_match,
                ) in groups:
                    with self.subTest(language=language, group=group_name):
                        match = re.search(
                            rf'<section data-tag-group="{group_name}">'
                            r"(.*?)</section>",
                            html,
                            re.DOTALL,
                        )
                        self.assertIsNotNone(match)
                        group = match.group(1)
                        self.assertEqual(1, group.count("data-post-list"))
                        self.assertEqual(1, group.count("data-post-search"))
                        self.assertEqual(2, group.count("data-post-item"))
                        self.assertNotIn("data-post-count", group)
                        self.assertIn(
                            f'data-count-one="{count_one}"',
                            group,
                        )
                        self.assertIn(
                            f'data-count-many="{count_many}"',
                            group,
                        )
                        self.assertIn(
                            f'placeholder="{placeholder}"',
                            group,
                        )
                        self.assertIn(no_match, group)
                        self.assertIn("data-search-empty", group)
                        self.assertIn("data-search-status", group)
                        self.assertIn('role="status"', group)
                        self.assertIn('aria-live="polite"', group)
                        self.assertIn('aria-atomic="true"', group)




    def test_filtered_post_rows_override_list_display_rules(self):
        site_css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
        hidden_rule = re.search(
            r"ul\.blog-posts li\[hidden\]\s*\{([^}]*)\}",
            site_css,
            re.DOTALL,
        )

        self.assertIsNotNone(hidden_rule)
        self.assertRegex(
            hidden_rule.group(1),
            r"display:\s*none\s*!important;",
        )

    def test_grouped_lists_use_localized_dates_without_repeating_year(self):
        with TemporaryDirectory() as temporary:
            for name, base_url in (
                ("root", "https://example.test/"),
                ("project", "https://example.test/example-blog/"),
            ):
                public = Path(temporary) / name
                build_site(
                    public,
                    base_url,
                    "--config",
                    "hugo.toml,tests/fixtures/interactions.toml",
                    "--contentDir",
                    "tests/fixtures/content",
                )
                english_blog = read_html(public, "blog/index.html")
                chinese_blog = read_html(public, "zh/blog/index.html")
                english_tag = read_html(public, "tags/fixture/index.html")
                chinese_tag = read_html(public, "zh/tags/测试/index.html")
                english_article = read_html(
                    public, "p/shared-article/index.html"
                )
                chinese_article = read_html(
                    public, "zh/p/shared-article/index.html"
                )

                for html in (english_blog, english_tag):
                    self.assertIn(
                        '<time datetime="2026-08-08">Aug 8</time>', html
                    )
                    self.assertNotIn(
                        '<time datetime="2026-08-08">August 8</time>',
                        html,
                    )
                    self.assertNotIn(
                        '<time datetime="2026-08-08">August 8, 2026</time>',
                        html,
                    )
                    self.assertIn(
                        '<li class="post-year" data-post-year="2026"><h3>2026</h3></li>',
                        html,
                    )
                self.assertIn(
                    '<time datetime="2026-08-09">Aug 9</time>',
                    english_tag,
                )

                for html in (chinese_blog, chinese_tag):
                    self.assertIn(
                        '<time datetime="2026-08-08">8月8日</time>', html
                    )
                    self.assertNotIn(
                        '<time datetime="2026-08-08">2026年8月8日</time>',
                        html,
                    )
                    self.assertIn(
                        '<li class="post-year" data-post-year="2026"><h3>2026</h3></li>',
                        html,
                    )
                self.assertIn(
                    '<time datetime="2026-08-09">8月9日</time>',
                    chinese_tag,
                )

                for html, count_one, count_many in (
                    (english_blog, "{count} post", "{count} posts"),
                    (chinese_blog, "{count} 篇文章", "{count} 篇文章"),
                ):
                    self.assertNotIn("data-post-count", html)
                    self.assertIn("data-post-search", html)
                    self.assertRegex(html, r"js/post-search\.")
                    self.assertIn(f'data-count-one="{count_one}"', html)
                    self.assertIn(f'data-count-many="{count_many}"', html)

                self.assertIn(
                    '<time datetime="2026-08-08">August 8, 2026</time>',
                    english_article,
                )
                self.assertNotIn("Published August 8, 2026", english_article)
                self.assertIn(
                    '<time datetime="2026-08-08">2026年8月8日</time>',
                    chinese_article,
                )
                self.assertNotIn("发布于", chinese_article)

            ungrouped_config = Path(temporary) / "ungrouped.toml"
            ungrouped_config.write_text(
                "[params]\ngroupByYear = false\n",
                encoding="utf-8",
            )
            ungrouped_public = Path(temporary) / "ungrouped"
            build_site(
                ungrouped_public,
                "https://example.test/",
                "--config",
                f"hugo.toml,{ungrouped_config}",
                "--contentDir",
                "tests/fixtures/content",
            )
            english_ungrouped = read_html(
                ungrouped_public, "blog/index.html"
            )
            chinese_ungrouped = read_html(
                ungrouped_public, "zh/blog/index.html"
            )

            for html in (english_ungrouped, chinese_ungrouped):
                self.assertNotIn('class="post-year"', html)
            self.assertIn(
                '<time datetime="2026-08-08">August 8, 2026</time>',
                english_ungrouped,
            )
            self.assertIn(
                '<time datetime="2026-08-08">2026年8月8日</time>',
                chinese_ungrouped,
            )

    def test_grouped_list_abbreviates_all_month_names(self):
        # The grouped date column uses consistent three-character month names.
        expected = {
            "2025-01-22": "Jan 22",
            "2025-02-22": "Feb 22",
            "2025-03-22": "Mar 22",
            "2025-04-22": "Apr 22",
            "2025-05-22": "May 22",
            "2025-06-22": "Jun 22",
            "2025-07-22": "Jul 22",
            "2025-08-22": "Aug 22",
            "2025-09-22": "Sep 22",
            "2025-10-22": "Oct 22",
            "2025-11-22": "Nov 22",
            "2025-12-22": "Dec 22",
        }
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            content.mkdir()
            (content / "_index.en.md").write_text(
                '+++\ntitle = "Fixture Home"\n+++\n\nFixture home.\n',
                encoding="utf-8",
            )
            (content / "_index.zh.md").write_text(
                '+++\ntitle = "测试首页"\n+++\n\n测试首页。\n',
                encoding="utf-8",
            )
            for month in range(1, 13):
                bundle = content / "blog" / f"month-{month:02d}"
                bundle.mkdir(parents=True)
                (bundle / "index.en.md").write_text(
                    "+++\n"
                    f'title = "Month {month:02d}"\n'
                    f"date = 2025-{month:02d}-22\n"
                    "draft = false\n"
                    f'interactionId = "month-{month:02d}"\n'
                    "+++\n\nBody.\n",
                    encoding="utf-8",
                )

            public = temporary_root / "root"
            build_site(
                public,
                "https://example.test/",
                "--contentDir",
                str(content),
            )
            listing = read_html(public, "blog/index.html")
            for stamp, rendered in expected.items():
                with self.subTest(date=stamp):
                    self.assertIn(
                        f'<time datetime="{stamp}">{rendered}</time>', listing
                    )
            # Article pages keep the full publication date.
            self.assertIn(
                '<time datetime="2025-11-22">November 22, 2025</time>',
                read_html(public, "p/month-11/index.html"),
            )

    def test_populated_multilingual_post_and_tag_pages(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            fixtures = {
                "blog/newer/index.en.md": """+++
title = "Newer visible post"
slug = "newer"
date = 2026-08-09
draft = false
tags = ["MixedCase"]
interactionId = "newer-visible-post"
+++

Visible English content.

## Article outline

More article words for the word count.
""",
                "blog/newer/index.zh.md": """+++
title = "中文可见文章"
slug = "newer"
date = 2026-08-09
draft = false
tags = ["MixedCase"]
interactionId = "newer-visible-post"
+++

中文可见内容。
""",
                "blog/older/index.en.md": """+++
title = "Older visible post"
date = 2024-01-02
draft = false
tags = ["MixedCase"]
interactionId = "older-visible-post"
+++

Older visible content.
""",
                "blog/hidden/index.en.md": """+++
title = "Hidden post"
date = 2025-03-04
draft = false
hidden = true
tags = ["MixedCase"]
interactionId = "hidden-post"
+++

Hidden content.
""",
            }
            for relative, source in fixtures.items():
                path = content / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            public = temporary_root / "public"
            build_site(
                public,
                "https://example.test/",
                "--contentDir",
                str(content),
            )
            english_blog = read_html(public, "blog/index.html")
            chinese_blog = read_html(public, "zh/blog/index.html")
            taxonomy = read_html(public, "tags/index.html")
            term = read_html(public, "tags/mixedcase/index.html")
            article = read_html(public, "p/newer/index.html")
            sitemap = ET.parse(public / "en/sitemap.xml").getroot()
            sitemap_locations = {
                node.findtext("{*}loc")
                for node in sitemap.findall("{*}url")
            }

            with self.subTest("English list has search and module without visible count"):
                self.assertIn("data-post-search", english_blog)
                self.assertRegex(
                    english_blog,
                    r'<script type="module" src="/js/post-search\.[^"]+\.mjs" integrity="sha256-[^"]+"></script>',
                )
                self.assertEqual(2, english_blog.count("data-post-item"))
                self.assertNotIn("data-post-count", english_blog)
                self.assertIn('data-count-one="{count} post"', english_blog)
                self.assertIn('data-count-many="{count} posts"', english_blog)
                self.assertIn('placeholder="Search..."', english_blog)
                self.assertIn("No matching posts", english_blog)
                self.assertNotIn("Hidden post", english_blog)

            with self.subTest("English list is reverse chronological by year"):
                self.assertLess(
                    english_blog.index('<li class="post-year" data-post-year="2026">'),
                    english_blog.index("Newer visible post"),
                )
                self.assertLess(
                    english_blog.index("Newer visible post"),
                    english_blog.index('<li class="post-year" data-post-year="2024">'),
                )
                self.assertLess(
                    english_blog.index('<li class="post-year" data-post-year="2024">'),
                    english_blog.index("Older visible post"),
                )

            with self.subTest("Chinese list omits visible count but retains count templates"):
                self.assertEqual(1, chinese_blog.count("data-post-item"))
                self.assertNotIn("data-post-count", chinese_blog)
                self.assertIn('data-count-one="{count} 篇文章"', chinese_blog)
                self.assertIn('data-count-many="{count} 篇文章"', chinese_blog)
                self.assertIn('placeholder="搜索..."', chinese_blog)
                self.assertIn("没有匹配的文章", chinese_blog)

            with self.subTest("taxonomy count excludes hidden posts"):
                self.assertIn(
                    '<a href="/tags/mixedcase/">#MixedCase</a>'
                    '<span class="tag-list-count">2</span>',
                    taxonomy,
                )
                self.assertNotIn(
                    '<span class="tag-list-count">3</span>',
                    taxonomy,
                )

            with self.subTest("term list excludes hidden posts"):
                self.assertIn("Newer visible post", term)
                self.assertIn("Older visible post", term)
                self.assertNotIn("Hidden post", term)

            with self.subTest("sitemap excludes hidden posts but keeps structure"):
                self.assertNotIn(
                    "https://example.test/p/hidden/",
                    sitemap_locations,
                )
                self.assertIn(
                    "https://example.test/p/newer/",
                    sitemap_locations,
                )
                self.assertIn(
                    "https://example.test/blog/",
                    sitemap_locations,
                )
                self.assertIn(
                    "https://example.test/tags/",
                    sitemap_locations,
                )

            with self.subTest("article renders content, tag, TOC, and word count"):
                self.assertRegex(article, r'<article data-word-count="\d+">')
                self.assertIn("Visible English content.", article)
                self.assertIn('<a href="/tags/mixedcase/">#MixedCase</a>', article)
                self.assertIn('class="toc-nav"', article)
                self.assertIn("Article outline", article)

            with self.subTest("search status is an atomic polite live region"):
                self.assertIn("data-search-status", english_blog)
                self.assertIn('role="status"', english_blog)
                self.assertIn('aria-live="polite"', english_blog)
                self.assertIn('aria-atomic="true"', english_blog)

            css = (ROOT / "assets" / "css" / "site.css").read_text(encoding="utf-8")
            with self.subTest("mobile search avoids automatic iOS zoom"):
                self.assertRegex(
                    css,
                    r"(?s)@media\s*\(max-width:\s*\d+px\)\s*\{.*?"
                    r"\[data-post-search\]\s*\{[^}]*font-size:\s*16px",
                )

    def test_taxonomy_with_only_hidden_posts_uses_empty_state(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            content = temporary_root / "content"
            bundle = content / "blog" / "hidden-only"
            bundle.mkdir(parents=True)
            (bundle / "index.en.md").write_text(
                """+++
title = "Hidden only post"
date = 2026-08-09
draft = false
hidden = true
tags = ["HiddenOnly"]
interactionId = "hidden-only-post"
+++

Hidden content.
""",
                encoding="utf-8",
            )
            public = temporary_root / "public"
            build_site(
                public,
                "https://example.test/",
                "--contentDir",
                str(content),
            )
            taxonomy = read_html(public, "tags/index.html")
            self.assertIn("No tags yet", taxonomy)
            self.assertNotIn("HiddenOnly", taxonomy)
            sitemap = ET.parse(public / "en/sitemap.xml").getroot()
            sitemap_locations = {
                node.findtext("{*}loc")
                for node in sitemap.findall("{*}url")
            }
            self.assertNotIn(
                "https://example.test/tags/hiddenonly/",
                sitemap_locations,
            )
            self.assertIn("https://example.test/", sitemap_locations)
            self.assertIn("https://example.test/blog/", sitemap_locations)
            self.assertIn("https://example.test/tags/", sitemap_locations)

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
