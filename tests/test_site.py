from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest


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
