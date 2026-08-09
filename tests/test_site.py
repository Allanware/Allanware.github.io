from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import tomllib
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ISTANBUL_IMAGE_ALTS = (
    ("unnamed-chunk-3-1.png", "Starting-eleven market values for AC Milan and Liverpool"),
    ("unnamed-chunk-3-2.png", "Ten highest-valued players across both starting elevens"),
    ("timeline.png", "Timeline of the 2005 Champions League final"),
    ("unnamed-chunk-9-1.png", "First-half shot map for AC Milan and Liverpool"),
    ("unnamed-chunk-10-1.png", "Second-half shot map for Liverpool and AC Milan"),
    ("unnamed-chunk-11-1.png", "Extra-time shot map for Liverpool and AC Milan"),
    ("unnamed-chunk-12-1.png", "Picture 1: AC Milan passing map for minutes 1 through 24"),
    ("unnamed-chunk-12-2.png", "Picture 2: AC Milan passing map after minute 24"),
    ("unnamed-chunk-12-3.png", "Picture 3: Liverpool passing map for minutes 1 through 24"),
    ("unnamed-chunk-12-4.png", "Picture 4: Liverpool passing map after minute 24"),
    ("unnamed-chunk-13-1.png", "Picture 1: AC Milan passing network during the six-minute spell"),
    ("unnamed-chunk-13-2.png", "Picture 2: AC Milan individual passes during the six-minute spell"),
    ("unnamed-chunk-13-3.png", "Picture 3: Liverpool passing network during the six-minute spell"),
    ("unnamed-chunk-13-4.png", "Picture 4: Liverpool individual passes during the six-minute spell"),
    ("unnamed-chunk-14-1.png", "Picture 1: Liverpool defensive actions during the six-minute spell"),
    ("unnamed-chunk-14-2.png", "Picture 2: AC Milan defensive actions during the six-minute spell"),
    ("unnamed-chunk-15-1.png", "Picture 1: AC Milan average first-half positions"),
    ("unnamed-chunk-15-2.png", "Picture 2: Liverpool average first-half positions"),
    ("unnamed-chunk-16-1.png", "Picture 1: AC Milan average early second-half positions"),
    ("unnamed-chunk-16-2.png", "Picture 2: Liverpool average early second-half positions"),
)


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


def alternate_link_entries(html: str) -> list[tuple[str, str]]:
    return re.findall(
        r'<link[^>]+rel="alternate"[^>]+hreflang="([^"]+)"[^>]+href="([^"]+)"',
        html,
    )


def alternate_links(html: str) -> set[tuple[str, str]]:
    return set(alternate_link_entries(html))


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
    def test_seo_uses_only_real_translations(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            unpaired = read_html(public, "p/beyond-the-cloud/index.html")
            self.assertEqual(set(), alternate_links(unpaired))
            self.assertEqual([], alternate_link_entries(unpaired))
            beyond_descriptions = metadata_descriptions(unpaired)
            for selector, values in beyond_descriptions.items():
                with self.subTest(metadata_selector=selector):
                    self.assertEqual(1, len(values))
            self.assertEqual(
                1,
                len({values[0] for values in beyond_descriptions.values()}),
            )
            beyond_description = next(iter(beyond_descriptions.values()))[0]
            self.assertIn(
                "A general challenge in information visualization",
                beyond_description,
            )
            self.assertIn("p<.001", beyond_description)
            self.assertNotEqual(
                "Wenxuan Zhao ; Karen B. Schloss",
                beyond_description.strip(),
            )

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
            self.assertIn('<p data-post-count>1 post</p>', english_posts)
            self.assertIn('data-count-one="{count} post"', english_posts)
            self.assertIn('data-count-many="{count} posts"', english_posts)
            self.assertIn('<p data-post-count>2 篇文章</p>', chinese_posts)
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
            production = temporary_root / "production"
            build_site(production, "https://example.test/")
            production_post = read_html(
                production,
                "p/beyond-the-cloud/index.html",
            )
            self.assertNotIn("giscus.app/client.js", production_post)

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
                "published blog posts require interactionId",
            ),
            (
                "missing-with-language-fallback",
                "tests/fixtures/missing-id-content",
                "hugo.toml,tests/fixtures/language-id.toml",
                "published blog posts require interactionId",
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
        page = (ROOT / "layouts/blog/page.html").read_text(encoding="utf-8")
        self.assertEqual(1, identity.count("return $result"))
        self.assertRegex(identity, r'isset\s+\$page\.Params\s+"interactionid"')
        self.assertNotRegex(identity, r'\$page\.Param\b')
        self.assertIn("$page.Translations", identity)
        self.assertNotIn("$page.AllTranslations", identity)
        self.assertEqual(1, page.count('partial "interaction-id.html" .'))
        self.assertEqual(
            1,
            page.count(
                'partial "giscus.html" '
                '(dict "Page" . "Entity" $interactionEntity)'
            ),
        )

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

    def test_rss_is_separate_and_localized(self):
        configuration = tomllib.loads((ROOT / "hugo.toml").read_text())
        self.assertEqual(10, configuration["services"]["rss"]["limit"])
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            english = ET.parse(public / "index.xml").getroot().find("channel")
            chinese = ET.parse(public / "zh/index.xml").getroot().find("channel")
            self.assertIsNotNone(english)
            self.assertIsNotNone(chinese)
            self.assertEqual("en-US", english.findtext("language"))
            self.assertEqual("zh-CN", chinese.findtext("language"))
            english_titles = [
                item.findtext("title") for item in english.findall("item")
            ]
            self.assertEqual(
                [
                    "Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts",
                    "Shapes and Functions of the Lekythos",
                    "The Miracle of Istanbul",
                ],
                english_titles,
            )
            self.assertEqual([], chinese.findall("item"))
            self.assertIn(
                "Recent posts from Wenxuan Zhao",
                english.findtext("description"),
            )
            self.assertIn("赵文轩的最新文章", chinese.findtext("description"))
            self.assertIn("30 May 2024", english.findtext("lastBuildDate"))
            zh_home = read_html(public, "zh/index.html")
            self.assertIn('href="https://example.test/zh/index.xml"', zh_home)
            self.assertIn('href="/zh/index.xml"', zh_home)

            limited = Path(temporary) / "limited"
            build_site(
                limited,
                "https://example.test/",
                "--config",
                "hugo.toml,tests/fixtures/rss-limit.toml",
            )
            limited_channel = ET.parse(limited / "index.xml").getroot().find(
                "channel"
            )
            self.assertEqual(
                [
                    "Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts",
                    "Shapes and Functions of the Lekythos",
                ],
                [
                    item.findtext("title")
                    for item in limited_channel.findall("item")
                ],
            )

            project = Path(temporary) / "project"
            build_site(project, "https://example.test/project/")
            project_channel = ET.parse(project / "index.xml").getroot().find(
                "channel"
            )
            project_prefix = "https://example.test/project/"
            self.assertEqual(project_prefix, project_channel.findtext("link"))
            atom_self = project_channel.find(
                "{http://www.w3.org/2005/Atom}link"
            )
            self.assertEqual(project_prefix + "index.xml", atom_self.get("href"))
            for item in project_channel.findall("item"):
                self.assertTrue(item.findtext("link").startswith(project_prefix))
                self.assertTrue(item.findtext("guid").startswith(project_prefix))

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

    def test_beyond_the_cloud_bundle_route_is_stable_across_base_urls(self):
        title_derived_route = (
            "p/beyond-the-cloud-a-perceptual-illusion-in-overlaid-bar-charts"
        )
        stable_route = "p/beyond-the-cloud"
        pdf_name = "beyond_the_cloud.v5.pdf"

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            cases = (
                ("root", "https://example.test/", "/p/beyond-the-cloud/"),
                (
                    "project",
                    "https://example.test/project/",
                    "/project/p/beyond-the-cloud/",
                ),
            )
            for name, base_url, href_prefix in cases:
                with self.subTest(base_url=name):
                    public = temporary_root / name / "public"
                    build_site(public, base_url)

                    article = public / stable_route / "index.html"
                    pdf = public / stable_route / pdf_name
                    self.assertTrue(article.is_file(), article)
                    self.assertTrue(pdf.is_file(), pdf)
                    self.assertFalse((public / title_derived_route).exists())
                    self.assertIn(
                        f'href="{href_prefix}{pdf_name}"',
                        article.read_text(encoding="utf-8"),
                    )

    def test_lekythos_bundle_route_and_images_are_stable_across_base_urls(self):
        stable_route = "p/lekythos-a-shape"
        expected_images = (
            ("front.jpeg", "Front view of the lekythos beside another vessel", 400),
            ("detail.jpeg", "Detail of the painted scene", 400),
            ("inner.jpg", "Interior vessel inside the lekythos", 200),
        )

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            cases = (
                ("root", "https://example.test/", "/p/lekythos-a-shape/"),
                (
                    "project",
                    "https://example.test/project/",
                    "/project/p/lekythos-a-shape/",
                ),
            )
            for name, base_url, href_prefix in cases:
                with self.subTest(base_url=name):
                    public = temporary_root / name / "public"
                    build_site(public, base_url)
                    article_path = public / stable_route / "index.html"
                    self.assertTrue(article_path.is_file(), article_path)
                    article = article_path.read_text(encoding="utf-8")
                    parser = MarkupReviewParser()
                    parser.feed(article)
                    self.assertEqual([False, False, False], parser.figures_in_paragraph)

                    for image_name, alt, width in expected_images:
                        resource = public / stable_route / image_name
                        self.assertTrue(resource.is_file(), resource)
                        self.assertRegex(
                            article,
                            rf'<img\s+src="{re.escape(href_prefix + image_name)}"'
                            rf'\s+alt="{re.escape(alt)}"\s+width="{width}"',
                        )

    def test_istanbul_bundle_route_and_resources_are_stable_across_base_urls(self):
        stable_route = "p/the-miracle-of-istanbul"
        rmd_name = "2021-03-04-The-Miracle-of-Istanbul.Rmd"

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            cases = (
                ("root", "https://example.test/", "/p/the-miracle-of-istanbul/"),
                (
                    "project",
                    "https://example.test/project/",
                    "/project/p/the-miracle-of-istanbul/",
                ),
            )
            for name, base_url, href_prefix in cases:
                with self.subTest(base_url=name):
                    public = temporary_root / name / "public"
                    build_site(public, base_url)
                    article_path = public / stable_route / "index.html"
                    self.assertTrue(article_path.is_file(), article_path)
                    article = article_path.read_text(encoding="utf-8")

                    rmd = public / stable_route / rmd_name
                    self.assertTrue(rmd.is_file(), rmd)
                    self.assertIn(f'href="{href_prefix}{rmd_name}"', article)
                    bundle_rmd = (
                        ROOT / "content" / "blog" / "the-miracle-of-istanbul" / rmd_name
                    ).read_bytes()
                    source_rmd = (ROOT / "writings-images" / rmd_name).read_bytes()
                    self.assertEqual(source_rmd, bundle_rmd)
                    self.assertEqual(bundle_rmd, rmd.read_bytes())

                    parser = MarkupReviewParser()
                    parser.feed(article)
                    self.assertEqual(20, len(parser.figures_in_paragraph))
                    self.assertEqual([False] * 20, parser.figures_in_paragraph)
                    self.assertEqual(20, len(parser.figure_images))

                    paragraphs = [
                        ("".join(text), in_blockquote)
                        for text, in_blockquote in zip(
                            parser.paragraph_texts,
                            parser.paragraphs_in_blockquote,
                            strict=True,
                        )
                    ]
                    for analysis_opening in ("In the 2nd half", "Surprisingly"):
                        with self.subTest(analysis_opening=analysis_opening):
                            matches = [
                                in_blockquote
                                for text, in_blockquote in paragraphs
                                if analysis_opening in text
                            ]
                            self.assertEqual([False], matches)
                    visible_picture_labels = [
                        "".join(text).strip()
                        for text in parser.emphasis_texts
                        if re.fullmatch(
                            r"picture [1-4]",
                            "".join(text).strip(),
                            re.IGNORECASE,
                        )
                    ]
                    with self.subTest("redundant picture labels are not visible"):
                        self.assertEqual([], visible_picture_labels)

                    for index, (image_name, alt) in enumerate(ISTANBUL_IMAGE_ALTS):
                        resource = public / stable_route / image_name
                        self.assertTrue(resource.is_file(), resource)
                        self.assertIn(f'src="{href_prefix}{image_name}"', article)
                        nonempty_alts = [
                            image.get("alt")
                            for image in parser.figure_images[index]
                            if image.get("alt")
                        ]
                        self.assertEqual([alt], nonempty_alts)

                    for archive_only in ("cover.png", "3-3.jpeg"):
                        self.assertFalse(
                            (public / stable_route / archive_only).exists(),
                            archive_only,
                        )
                        self.assertNotIn(href_prefix + archive_only, article)

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

    def test_initial_chinese_lists_are_valid_and_empty(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            posts = read_html(public, "zh/blog/index.html")
            tags = read_html(public, "zh/tags/index.html")
            self.assertIn("暂无文章", posts)
            self.assertIn("暂无标签", tags)
            self.assertNotIn("No posts yet", posts)
            self.assertNotIn("No tags yet", tags)

    def test_post_search_has_localized_no_match_feedback(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            english = read_html(public, "blog/index.html")
            self.assertIn('data-search-empty', english)
            self.assertIn("No matching posts", english)

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

            with self.subTest("English list has search, module, and visible count"):
                self.assertIn("data-post-search", english_blog)
                self.assertRegex(
                    english_blog,
                    r'<script type="module" src="/js/post-search\.[^"]+\.mjs" integrity="sha256-[^"]+"></script>',
                )
                self.assertEqual(2, english_blog.count("data-post-item"))
                self.assertIn("<p data-post-count>2 posts</p>", english_blog)
                self.assertIn('data-count-one="{count} post"', english_blog)
                self.assertIn('data-count-many="{count} posts"', english_blog)
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

            with self.subTest("Chinese list uses invariant singular count"):
                self.assertEqual(1, chinese_blog.count("data-post-item"))
                self.assertIn("<p data-post-count>1 篇文章</p>", chinese_blog)

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
