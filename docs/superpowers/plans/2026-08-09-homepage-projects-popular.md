# Homepage Projects and Live Popular Posts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build localized `Where Was I` / `说哪儿了` homepages with the supplied drawing as the tab icon, language-local projects and latest posts, live Kudos-ranked popular posts, and project-first tag results while preserving the Beyond page URL and interactions.

**Architecture:** Move Beyond into a first-class `projects` section while sharing one article partial with blog posts and preserving `/p/beyond-the-cloud/` plus `post:beyond-the-cloud`. Hugo renders static intro, project, and latest lists; a separate count-only ES module ranks hidden current-language blog candidates in the browser. A reusable strict Kudos configuration partial serves both the article widget and homepage ranking, while term pages split their existing archive lists by section.

**Tech Stack:** Hugo 0.164 templates and multilingual content, TOML, Hugo Pipes image processing and fingerprinting, vanilla ES modules, Python 3.11+ standard-library `unittest`, Node 22+ `node:test`, GitHub Pages Actions, Cloudflare Kudos Worker v0.2.0.

Hugo-specific steps use the current official
[build-options](https://gohugo.io/content-management/build-options/) and
[image-processing](https://gohugo.io/content-management/image-processing/)
contracts verified on 2026-08-09.

---

## File Map

- `assets/images/drawing-hands.png`: unchanged user-supplied 400×400 source artwork.
- `layouts/_partials/favicon.html`: site-local 32×32 and 180×180 Hugo image variants.
- `hugo.toml`: localized titles and matching `/p/` permalinks for `projects`.
- `content/_index.{en,zh}.md`: localized name/contact placeholder.
- `content/projects/_index.{en,zh}.md`: non-rendered project section roots; their regular descendants remain listable.
- `content/projects/beyond-the-cloud/*`: moved project bundle with `projectStatus = "past"`.
- `layouts/_partials/article.html`: shared post/project article body and interactions.
- `layouts/{blog,projects}/page.html`: thin content-type entry points.
- `scripts/validate_interaction_ids.py`: cross-section interaction validation.
- `scripts/new_translation.py`: safe `blog` or `projects` translation creation.
- `layouts/home.html`: semantic homepage composition.
- `layouts/_partials/home-title-list.html`: title-only list renderer.
- `layouts/_partials/kudos-config.html`: one strict reusable endpoint guard.
- `layouts/_partials/popular-posts.html`: inert candidates and runtime states.
- `assets/js/popular-posts.mjs`: count-only loading, validation, ranking, and rendering.
- `layouts/_partials/post-list.html`: parameterized visible labels for posts or projects.
- `layouts/term.html`: Projects-first, Posts-second tag results.
- `assets/css/site.css`: homepage title-list and state styling.
- `i18n/{en,zh}.toml`: all new labels and accessible states.
- `tests/popular-posts.test.mjs`: dependency-free ranking/controller tests.
- `tests/fixtures/content/projects/**`: multilingual project/tag integration fixture.
- `tests/test_{site,content,interaction_ids,new_translation,authoring,repository}.py`: generated output, migration, validation, authoring, and provenance contracts.
- `tests/post-search.test.mjs`: independent project/post tag-group filtering.
- `README.md`: projects, homepage ranking privacy, and local CORS guidance.

The untracked migration inputs `beyond-the-cloud.md`, `lekythos-a-shape.md`,
`the-miracle-of-istanbul.md`, and `writings-images/` are never moved, edited,
staged, or committed. Only the separate supplied `drawing_hands.png` is moved
into the tracked assets tree.

## Execution Preconditions

Execute the implementation on branch `feat/homepage-projects-popular` in the
dedicated worktree `/private/tmp/blog-homepage-projects-popular`, created from
the commit containing this plan:

```bash
git worktree add /private/tmp/blog-homepage-projects-popular \
  -b feat/homepage-projects-popular
mv /Users/allan/GitHub/blog/drawing_hands.png \
  /private/tmp/blog-homepage-projects-popular/drawing_hands.png
cd /private/tmp/blog-homepage-projects-popular
shasum -a 256 drawing_hands.png
```

Expected image digest:

```text
8a1a3fb3abaca3e1cffdd110d203892c02052bd1196398730de6db6e3955c8e8
```

Do not copy the four migration inputs into the worktree; the committed bundles
and hermetic tests are the implementation inputs.

### Task 1: Localized Brand, Contact Intro, and Tab Icon

**Files:**
- Move: `drawing_hands.png` → `assets/images/drawing-hands.png`
- Create: `layouts/_partials/favicon.html`
- Modify: `hugo.toml`
- Modify: `content/_index.en.md`
- Modify: `content/_index.zh.md`
- Modify: `layouts/home.html`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Add the PNG-dimension helper and failing generated-site test**

Add this standard-library helper near `read_html` in `tests/test_site.py`:

```python
def png_dimensions(path: Path) -> tuple[int, int]:
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise AssertionError(f"not a PNG: {path}")
    return tuple(int.from_bytes(payload[offset : offset + 4], "big") for offset in (16, 20))
```

Add this test to `GeneratedSiteTests`:

```python
def test_localized_brand_contact_and_generated_favicons(self):
    source = ROOT / "assets/images/drawing-hands.png"
    self.assertTrue(source.is_file())
    self.assertEqual(
        "8a1a3fb3abaca3e1cffdd110d203892c02052bd1196398730de6db6e3955c8e8",
        hashlib.sha256(source.read_bytes()).hexdigest(),
    )
    self.assertEqual((400, 400), png_dimensions(source))

    configuration = tomllib.loads((ROOT / "hugo.toml").read_text(encoding="utf-8"))
    self.assertEqual("Where Was I", configuration["languages"]["en"]["title"])
    self.assertEqual("说哪儿了", configuration["languages"]["zh"]["title"])

    cases = (
        ("root", "https://example.test/", "/"),
        ("project", "https://example.test/example-blog/", "/example-blog/"),
    )
    with TemporaryDirectory() as temporary:
        for name, base_url, base_path in cases:
            public = Path(temporary) / name
            build_site(public, base_url)
            pages = (
                (
                    "index.html", "Where Was I",
                    '<p>Wenxuan Zhao. <a href="mailto:xiaodoubizwx@gmail.com">Contact me</a>.</p>',
                ),
                (
                    "zh/index.html", "说哪儿了",
                    '<p>赵文轩。<a href="mailto:xiaodoubizwx@gmail.com">联系我</a>。</p>',
                ),
            )
            icon_hrefs = None
            for relative, title, intro in pages:
                html = read_html(public, relative)
                self.assertIn(f"<title>{title}</title>", html)
                self.assertIn(f"<h1>{title}</h1>", html)
                self.assertIn(intro, html)
                self.assertNotRegex(html, rf">[^<]*xiaodoubizwx@gmail\.com[^<]*<")
                matches = re.findall(
                    r'<link rel="(icon|apple-touch-icon)" type="image/png" '
                    r'sizes="(32x32|180x180)" href="([^"]+)">',
                    html,
                )
                self.assertEqual(2, len(matches))
                current_hrefs = {(kind, size): href for kind, size, href in matches}
                self.assertEqual(
                    {("icon", "32x32"), ("apple-touch-icon", "180x180")},
                    set(current_hrefs),
                )
                self.assertEqual(icon_hrefs or current_hrefs, current_hrefs)
                icon_hrefs = current_hrefs

            for (kind, size), href in icon_hrefs.items():
                self.assertTrue(href.startswith(base_path), href)
                relative_asset = urlsplit(href).path.removeprefix(base_path)
                asset = public / relative_asset
                self.assertTrue(asset.is_file(), href)
                expected = {
                    ("icon", "32x32"): 32,
                    ("apple-touch-icon", "180x180"): 180,
                }[(kind, size)]
                self.assertEqual((expected, expected), png_dimensions(asset))
```

- [ ] **Step 2: Run the focused test and observe RED**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_localized_brand_contact_and_generated_favicons -v
```

Expected: FAIL because `assets/images/drawing-hands.png` does not exist and the configured titles are still the author's name.

- [ ] **Step 3: Move the supplied source image without touching migration inputs**

Run:

```bash
mkdir -p assets/images
mv drawing_hands.png assets/images/drawing-hands.png
shasum -a 256 assets/images/drawing-hands.png
```

Expected digest:

```text
8a1a3fb3abaca3e1cffdd110d203892c02052bd1196398730de6db6e3955c8e8
```

- [ ] **Step 4: Implement the site-local favicon pipeline**

Create `layouts/_partials/favicon.html`:

```go-html-template
{{- $source := resources.Get "images/drawing-hands.png" -}}
{{- if not $source -}}
  {{- errorf "required favicon source assets/images/drawing-hands.png is missing" -}}
{{- end -}}
{{- $icon := $source.Resize "32x32 Lanczos" -}}
{{- $touch := $source.Resize "180x180 Lanczos" -}}
<link rel="icon" type="image/png" sizes="32x32" href="{{ $icon.RelPermalink }}">
<link rel="apple-touch-icon" type="image/png" sizes="180x180" href="{{ $touch.RelPermalink }}">
```

- [ ] **Step 5: Apply the exact localized titles and intros**

In `hugo.toml`, set:

```toml
[languages.en]
  title = "Where Was I"

[languages.zh]
  title = "说哪儿了"
```

Replace `content/_index.en.md` with:

```markdown
+++
title = "Where Was I"
+++

Wenxuan Zhao. [Contact me](mailto:xiaodoubizwx@gmail.com).
```

Replace `content/_index.zh.md` with:

```markdown
+++
title = "说哪儿了"
+++

赵文轩。[联系我](mailto:xiaodoubizwx@gmail.com)。
```

Add the home-only document title override before the existing `main` block in `layouts/home.html`:

```go-html-template
{{ define "title" }}{{ .Site.Title }}{{ end }}
```

- [ ] **Step 6: Run focused and chrome regression tests**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_localized_brand_contact_and_generated_favicons \
  tests.test_site.GeneratedSiteTests.test_localized_core_routes_exist \
  tests.test_site.GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference -v
```

Expected: 3 tests PASS. The pre-existing localized-route assertions continue
to find `Wenxuan Zhao`/`赵文轩` in the new intro, while the new test separately
locks the localized site and header titles.

- [ ] **Step 7: Commit the branding slice**

```bash
git add assets/images/drawing-hands.png layouts/_partials/favicon.html hugo.toml \
  content/_index.en.md content/_index.zh.md layouts/home.html tests/test_site.py
git commit -m "feat: add localized blog identity and favicon"
```

### Task 2: First-Class Projects and Preserved Beyond Identity

**Files:**
- Move: `content/blog/beyond-the-cloud/*` → `content/projects/beyond-the-cloud/*`
- Create: `content/projects/_index.en.md`
- Create: `content/projects/_index.zh.md`
- Create: `layouts/_partials/article.html`
- Create: `layouts/projects/page.html`
- Modify: `layouts/blog/page.html`
- Modify: `layouts/_partials/interaction-id.html`
- Modify: `hugo.toml`
- Modify: `scripts/validate_interaction_ids.py`
- Modify: `scripts/new_translation.py`
- Modify: `tests/test_content.py`
- Modify: `tests/test_interaction_ids.py`
- Modify: `tests/test_new_translation.py`
- Modify: `tests/test_repository.py`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Write failing project migration and URL/interaction tests**

In `tests/test_content.py`, replace the Beyond constants with:

```python
PROJECTS = ROOT / "content" / "projects"
BEYOND_THE_CLOUD = PROJECTS / "beyond-the-cloud"
BEYOND_THE_CLOUD_POST = BEYOND_THE_CLOUD / "index.en.md"
```

Change the exact Beyond front-matter assertion to:

```python
self.assertEqual(
    set(front_matter),
    {"title", "date", "lastmod", "draft", "tags", "interactionId", "projectStatus"},
)
self.assertEqual("past", front_matter["projectStatus"])
```

Add this generated-site test:

```python
def test_beyond_is_a_project_with_a_stable_public_contract(self):
    with TemporaryDirectory() as temporary:
        for name, base_url, base_path in (
            ("root", "https://example.test/", "/"),
            ("project", "https://example.test/example-blog/", "/example-blog/"),
        ):
            public = Path(temporary) / name
            build_site(public, base_url)
            article = read_html(public, "p/beyond-the-cloud/index.html")
            self.assertFalse((public / "projects/index.html").exists())
            self.assertFalse((public / "zh/projects/index.html").exists())
            self.assertIn(
                f'<link rel="canonical" href="{base_url}p/beyond-the-cloud/">',
                article,
            )
            self.assertIn('data-term="post:beyond-the-cloud"', article)
            self.assertIn('data-kudos-entity="post:beyond-the-cloud"', article)
            self.assertIn(
                f'href="{base_path}p/beyond-the-cloud/beyond_the_cloud.v5.pdf"',
                article,
            )
            self.assertTrue(
                (public / "p/beyond-the-cloud/beyond_the_cloud.v5.pdf").is_file()
            )
            archive = read_html(public, "blog/index.html")
            self.assertNotIn("Beyond the Cloud", archive)
            self.assertIn('<p data-post-count>2 posts</p>', archive)
            rss_titles = [
                item.findtext("title")
                for item in ET.parse(public / "index.xml").getroot().find("channel").findall("item")
            ]
            self.assertNotIn(
                "Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts",
                rss_titles,
            )
            project_url = f"{base_url}p/beyond-the-cloud/"
            english_sitemap = ET.parse(public / "en/sitemap.xml").getroot()
            chinese_sitemap = ET.parse(public / "zh/sitemap.xml").getroot()
            english_locations = {
                node.text for node in english_sitemap.findall("{*}url/{*}loc")
            }
            chinese_locations = {
                node.text for node in chinese_sitemap.findall("{*}url/{*}loc")
            }
            self.assertIn(project_url, english_locations)
            self.assertNotIn(project_url, chinese_locations)
            self.assertNotIn(f"{base_url}projects/", english_locations)
            self.assertNotIn(f"{base_url}zh/projects/", chinese_locations)
```

Replace `test_interaction_identity_is_computed_once_from_page_local_params`
so the interaction calls are asserted in the new shared renderer and both
section entry points are proven thin:

```python
def test_interaction_identity_is_computed_once_from_page_local_params(self):
    identity_path = ROOT / "layouts/_partials/interaction-id.html"
    self.assertTrue(identity_path.is_file())
    identity = identity_path.read_text(encoding="utf-8")
    article = (ROOT / "layouts/_partials/article.html").read_text(encoding="utf-8")
    blog_page = (ROOT / "layouts/blog/page.html").read_text(encoding="utf-8")
    project_page = (ROOT / "layouts/projects/page.html").read_text(encoding="utf-8")
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
```

In `tests/test_repository.py`, move the derived-template provenance mapping
from the old blog entry point to the shared renderer:

```python
DERIVED_TEMPLATES = {
    "layouts/baseof.html": "layouts/_default/baseof.html",
    "layouts/404.html": "layouts/404.html",
    "layouts/_markup/render-image.html": "layouts/_default/_markup/render-image.html",
    "layouts/_markup/render-link.html": "layouts/_default/_markup/render-link.html",
    "layouts/_partials/header.html": "layouts/partials/header.html",
    "layouts/_partials/nav.html": "layouts/partials/nav.html",
    "layouts/_partials/footer.html": "layouts/partials/footer.html",
    "layouts/_partials/toc.html": "layouts/partials/toc.html",
    "layouts/_partials/custom_head.html": "layouts/partials/custom_head.html",
    "layouts/_partials/seo_tags.html": "layouts/partials/seo_tags.html",
    "layouts/_partials/post-list.html": "layouts/_default/list.html",
    "layouts/_partials/article.html": "layouts/_default/single.html",
    "layouts/blog/section.html": "layouts/_default/list.html",
    "layouts/home.rss.xml": "layouts/_default/rss.xml",
}
```

The thin `layouts/blog/page.html` and `layouts/projects/page.html` files contain
only site-local composition and therefore are not represented as upstream-
derived templates. The generated-site source test above locks their exact role.

- [ ] **Step 2: Write failing cross-section validator tests**

In `tests/test_interaction_ids.py`, add a `section="blog"` keyword to `write_post`, build paths under that section, and add:

```python
def test_project_translations_share_an_id(self):
    self.write_post("shared-project", "en", section="projects", interaction_id="shared-project")
    self.write_post("shared-project", "zh", section="projects", interaction_id="shared-project")
    self.assertEqual(validate_content(self.content_root), [])

def test_published_project_without_an_id_is_rejected(self):
    self.write_post("missing-project", "en", section="projects")
    errors = validate_content(self.content_root)
    self.assertEqual(1, len(errors))
    self.assertIn("interactionId is required for published articles", errors[0])

def test_project_translations_must_share_an_id(self):
    self.write_post(
        "mismatched-project",
        "en",
        section="projects",
        interaction_id="english-project",
    )
    self.write_post(
        "mismatched-project",
        "zh",
        section="projects",
        interaction_id="chinese-project",
    )
    errors = validate_content(self.content_root)
    self.assertEqual(1, len(errors))
    self.assertIn("translations in bundle", errors[0])
    self.assertIn("must share one interactionId", errors[0])

def test_blog_and_project_bundles_cannot_reuse_an_id(self):
    self.write_post("article", "en", section="blog", interaction_id="duplicate-id")
    self.write_post("project", "en", section="projects", interaction_id="duplicate-id")
    errors = validate_content(self.content_root)
    self.assertEqual(1, len(errors))
    self.assertIn("interactionId 'duplicate-id' is reused by bundles", errors[0])
```

In `tests/test_new_translation.py`, replace `make_source` with:

```python
def make_source(self, content: Path, *, section: str = "blog") -> Path:
    source = content / section / "my-post/index.en.md"
    source.parent.mkdir(parents=True)
    source.write_bytes(
        '+++\ninteractionId = "my-post"\n+++\n\nBody 中文\n'.encode("utf-8")
    )
    return source
```

Then add:

```python
def test_copies_a_project_translation_verbatim(self):
    with TemporaryDirectory() as temporary:
        content = Path(temporary)
        source = self.make_source(content, section="projects")
        target = create_translation(
            content, "my-post", "en", "zh", section="projects"
        )
        self.assertEqual(content / "projects/my-post/index.zh.md", target)
        self.assertEqual(source.read_bytes(), target.read_bytes())

def test_rejects_an_unknown_section(self):
    with TemporaryDirectory() as temporary:
        with self.assertRaisesRegex(ValueError, "section must be blog or projects"):
            create_translation(
                Path(temporary), "my-post", "en", "zh", section="pages"
            )
```

- [ ] **Step 3: Run the migration slice and observe RED**

Run:

```bash
python3 -m unittest \
  tests.test_content.MigratedContentTests.test_beyond_the_cloud_bundle \
  tests.test_interaction_ids \
  tests.test_new_translation \
  tests.test_repository.RepositoryTests.test_derived_templates_record_exact_upstream_sources \
  tests.test_site.GeneratedSiteTests.test_interaction_identity_is_computed_once_from_page_local_params \
  tests.test_site.GeneratedSiteTests.test_beyond_is_a_project_with_a_stable_public_contract -v
```

Expected: FAIL because Beyond is still under `content/blog`, the shared article
partial and project entry point do not exist, the validator scans only blog
bundles, and `create_translation` has no section argument.

- [ ] **Step 4: Move the complete Beyond bundle and add project roots**

Run:

```bash
mkdir -p content/projects
mv content/blog/beyond-the-cloud content/projects/beyond-the-cloud
```

Add this line to the Beyond TOML front matter without changing its body:

```toml
projectStatus = "past"
```

Create `content/projects/_index.en.md`:

```toml
+++
title = "Projects"
[build]
  render = "never"
+++
```

Create `content/projects/_index.zh.md`:

```toml
+++
title = "项目"
[build]
  render = "never"
+++
```

Hugo's documented `render = "never"` excludes the section page from rendering
and page collections. Because the option is not cascaded, descendant project
pages remain rendered and listable.

- [ ] **Step 5: Preserve the route and share the article renderer**

In `hugo.toml`, extend the permalink table:

```toml
[permalinks.page]
  blog = "/p/:contentbasename/"
  projects = "/p/:contentbasename/"
```

Create `layouts/_partials/article.html` with the complete shared renderer:

```go-html-template
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/_default/single.html */ -}}
<article data-word-count="{{ .WordCount }}">
  <header>
    <h2>{{ .Title }}</h2>
    {{ if not .Date.IsZero }}
      <p><time datetime="{{ .Date.Format "2006-01-02" }}">{{ T "publishedOn" (.Date | time.Format .Site.Params.dateFormat) }}</time></p>
    {{ end }}
  </header>
  <content>{{ .Content }}</content>
  {{ with .GetTerms "tags" }}
    <p class="post-tags">
      {{ range . }}<a href="{{ .RelPermalink }}">#{{ .LinkTitle }}</a> {{ end }}
    </p>
  {{ end }}
  {{ if .Site.Params.toc }}<div class="toc">{{ partial "toc.html" . }}</div>{{ end }}
  {{ $interactionEntity := partial "interaction-id.html" . }}
  {{ partial "kudos.html" (dict "Page" . "Entity" $interactionEntity) }}
  {{ partial "giscus.html" (dict "Page" . "Entity" $interactionEntity) }}
</article>
```

Replace `layouts/blog/page.html` with:

```go-html-template
{{ define "main" }}{{ partial "article.html" . }}{{ end }}
```

Create `layouts/projects/page.html` with the same entry point:

```go-html-template
{{ define "main" }}{{ partial "article.html" . }}{{ end }}
```

In `layouts/_partials/interaction-id.html`, change only the missing-ID error to content-neutral wording:

```go-html-template
{{- errorf "%s: published articles require interactionId" $page.File.Path -}}
```

Update direct-Hugo failure assertions in `tests/test_site.py` from “published blog posts” to “published articles.”

- [ ] **Step 6: Generalize the Python interaction validator**

In `scripts/validate_interaction_ids.py`, add:

```python
CONTENT_SECTIONS = ("blog", "projects")
```

Change the module and `validate_content` docstrings from “blog posts” to
“blog posts and projects” so the public API describes the expanded scan.

Replace the single glob loop with:

```python
paths = (
    path
    for section in CONTENT_SECTIONS
    for path in (content_root / section).glob("*/index.*.md")
)
for path in sorted(paths):
```

Change the missing-ID message to:

```python
f"{display_path}: interactionId is required for published articles"
```

In `test_published_post_without_an_id_is_rejected`, replace the expected
substring with `interactionId is required for published articles`.

Keep the existing `bundle_ids` and `id_bundles` dictionaries outside the section loop; this is what enforces cross-section uniqueness.

- [ ] **Step 7: Generalize safe translation copying**

In `scripts/new_translation.py`, add:

```python
SECTIONS = {"blog", "projects"}
```

Replace `create_translation` with this complete implementation:

```python
def create_translation(
    content_root: Path,
    slug: str,
    source_language: str,
    target_language: str,
    *,
    section: str = "blog",
) -> Path:
    """Exclusively copy one leaf-bundle language file to another language."""
    if SLUG_PATTERN.fullmatch(slug) is None:
        raise ValueError(
            "slug must contain lowercase letters, numbers, or internal hyphens"
        )
    if source_language not in LANGUAGES or target_language not in LANGUAGES:
        raise ValueError("languages must be en or zh")
    if source_language == target_language:
        raise ValueError("source and target languages must differ")
    if section not in SECTIONS:
        raise ValueError("section must be blog or projects")

    resolved_content_root = Path(content_root).resolve()
    section_path = Path(content_root) / section
    section_root = section_path.resolve()
    try:
        section_root.relative_to(resolved_content_root)
    except ValueError as error:
        raise ValueError(
            f"{section} content root must resolve inside content root"
        ) from error
    bundle = section_path / slug
    resolved_bundle = bundle.resolve()
    try:
        resolved_bundle.relative_to(section_root)
    except ValueError as error:
        raise ValueError(
            f"slug must resolve inside the {section} content root"
        ) from error

    source = bundle / f"index.{source_language}.md"
    target = bundle / f"index.{target_language}.md"
    if not source.is_file():
        raise FileNotFoundError(f"source translation does not exist: {source}")

    resolved_source = source.resolve()
    try:
        resolved_source.relative_to(resolved_bundle)
    except ValueError as error:
        raise ValueError("source translation must resolve inside its bundle") from error

    payload = resolved_source.read_bytes()
    try:
        with target.open("xb") as destination:
            destination.write(payload)
    except FileExistsError:
        raise FileExistsError(f"target translation already exists: {target}") from None
    return target
```

Add the CLI option and forward it:

```python
parser.add_argument("--section", choices=sorted(SECTIONS), default="blog")

target = create_translation(
    arguments.content_root,
    arguments.slug,
    arguments.source_language,
    arguments.target_language,
    section=arguments.section,
)
```

Import `subprocess` in `tests/test_new_translation.py`, define
`ROOT = Path(__file__).resolve().parents[1]`, and add the exact CLI regression:

```python
def test_cli_copies_a_project_translation(self):
    with TemporaryDirectory() as temporary:
        content = Path(temporary) / "content"
        source = self.make_source(content, section="projects")
        result = subprocess.run(
            [
                "python3",
                str(ROOT / "scripts/new_translation.py"),
                "my-post",
                "en",
                "zh",
                "--section",
                "projects",
                "--content-root",
                str(content),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        target = content / "projects/my-post/index.zh.md"
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(f"Created {target}", result.stdout)
        self.assertEqual(source.read_bytes(), target.read_bytes())
```

The function-level project test above covers byte equality, while the existing
blog test continues to prove exclusive overwrite refusal for the shared code
path.

- [ ] **Step 8: Turn the migration and RSS expectations GREEN**

In the production matrix, replace the one exact archive assertion
`<p data-post-count>3 posts</p>` with `<p data-post-count>2 posts</p>`. In
`test_rss_is_separate_and_localized`, use this English title list for both the
default and limit-two builds:

```python
[
    "Shapes and Functions of the Lekythos",
    "The Miracle of Istanbul",
]
```

Replace the RSS description expectations with `Recent posts from Where Was I`
and `说哪儿了的最新文章`. Replace the last-build-date substring `30 May 2024`
with `05 Nov 2023`, the newest `lastmod` among the two remaining blog posts.

Run:

```bash
python3 -m unittest tests.test_content tests.test_interaction_ids \
  tests.test_new_translation tests.test_authoring \
  tests.test_repository.RepositoryTests.test_derived_templates_record_exact_upstream_sources \
  tests.test_site.GeneratedSiteTests.test_interaction_identity_is_computed_once_from_page_local_params \
  tests.test_site.GeneratedSiteTests.test_beyond_is_a_project_with_a_stable_public_contract \
  tests.test_site.GeneratedSiteTests.test_rss_is_separate_and_localized \
  tests.test_site.GeneratedSiteTests.test_giscus_uses_shared_strict_threads_and_validated_configuration \
  tests.test_site.GeneratedSiteTests.test_kudos_uses_shared_entities_accessible_ssr_and_hashed_modules -v
```

Expected: all focused tests PASS with the same `/p/beyond-the-cloud/`, `post:beyond-the-cloud`, PDF bytes, Giscus thread, and Kudos widget.

- [ ] **Step 9: Commit the project content model**

```bash
git add content/blog content/projects layouts/blog/page.html layouts/projects/page.html \
  layouts/_partials/article.html layouts/_partials/interaction-id.html hugo.toml \
  scripts/validate_interaction_ids.py scripts/new_translation.py \
  tests/test_content.py tests/test_interaction_ids.py tests/test_new_translation.py \
  tests/test_repository.py tests/test_site.py
git commit -m "feat: promote Beyond to a project"
```

### Task 3: Static Homepage Projects and Latest Posts

**Files:**
- Create: `layouts/_partials/home-title-list.html`
- Modify: `layouts/home.html`
- Modify: `assets/css/site.css`
- Modify: `i18n/en.toml`
- Modify: `i18n/zh.toml`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Write failing production homepage structure tests**

Add:

```python
def test_home_sections_are_ordered_title_only_and_language_local(self):
    with TemporaryDirectory() as temporary:
        for name, base_url, base_path in (
            ("root", "https://example.test/", "/"),
            ("project", "https://example.test/example-blog/", "/example-blog/"),
        ):
            public = Path(temporary) / name
            build_site(public, base_url)
            english = read_html(public, "index.html")
            chinese = read_html(public, "zh/index.html")
            self.assertLess(english.index('class="home-intro"'), english.index('data-home-section="projects"'))
            self.assertLess(english.index('data-home-section="projects"'), english.index('data-home-section="latest"'))
            self.assertLess(english.index('data-home-section="latest"'), english.index('data-home-section="popular"'))
            self.assertRegex(english, r'<h2>Projects</h2>[\s\S]*<h3>Past projects</h3>')
            self.assertRegex(
                english,
                r'<section data-home-section="latest">\s*<h2>Latest posts</h2>',
            )
            self.assertRegex(
                english,
                r'<section data-home-section="popular">\s*<h2>Popular posts</h2>',
            )
            self.assertIn("Beyond the Cloud", english)
            self.assertNotIn("Beyond the Cloud", chinese)
            self.assertIn("暂无过往项目", chinese)

            latest = re.search(
                r'<section data-home-section="latest">(.*?)</section>', english, re.DOTALL
            ).group(1)
            self.assertIn(f'href="{base_path}p/lekythos-a-shape/"', latest)
            self.assertIn(f'href="{base_path}p/the-miracle-of-istanbul/"', latest)
            self.assertNotIn("Beyond the Cloud", latest)
            self.assertNotRegex(latest, r"<time|data-post-count|#visualization")
            self.assertEqual(2, latest.count("<li>"))

            self.assertRegex(chinese, r'<h2>项目</h2>[\s\S]*<h3>过往项目</h3>')
            self.assertLess(chinese.index('class="home-intro"'), chinese.index('data-home-section="projects"'))
            self.assertLess(chinese.index('data-home-section="projects"'), chinese.index('data-home-section="latest"'))
            self.assertLess(chinese.index('data-home-section="latest"'), chinese.index('data-home-section="popular"'))
            self.assertRegex(
                chinese,
                r'<section data-home-section="latest">\s*<h2>最新文章</h2>',
            )
            self.assertRegex(
                chinese,
                r'<section data-home-section="popular">\s*<h2>热门文章</h2>',
            )
            self.assertIn("暂无文章", chinese)
```

- [ ] **Step 2: Write a failing latest-limit fixture test**

Add this self-contained test:

```python
def test_home_latest_is_capped_at_three_visible_posts(self):
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        content = temporary_root / "content"
        content.mkdir()
        (content / "_index.en.md").write_text(
            '+++\ntitle = "Where Was I"\n+++\n\nFixture home.\n',
            encoding="utf-8",
        )
        (content / "_index.zh.md").write_text(
            '+++\ntitle = "说哪儿了"\n+++\n\n测试首页。\n',
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
            ("project", "https://example.test/example-blog/", "/example-blog/"),
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
            self.assertIsNotNone(latest_match)
            latest = latest_match.group(1)
            self.assertEqual(
                ["Post 4", "Post 3", "Post 2"],
                re.findall(r'<a[^>]*>([^<]+)</a>', latest),
            )
            self.assertIn(f'href="{base_path}p/post-4/"', latest)
            self.assertNotIn("Post 1", latest)
            self.assertNotIn("Hidden post", latest)
            self.assertNotIn("Draft post", latest)
            self.assertNotIn("Draft project", home)
```

- [ ] **Step 3: Run both homepage tests and observe RED**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_home_sections_are_ordered_title_only_and_language_local \
  tests.test_site.GeneratedSiteTests.test_home_latest_is_capped_at_three_visible_posts -v
```

Expected: FAIL because `home.html` still renders only `.Content`.

- [ ] **Step 4: Create the title-only list partial**

Create `layouts/_partials/home-title-list.html`:

```go-html-template
{{- $pages := .Pages -}}
{{- $emptyKey := .EmptyKey -}}
{{- if gt (len $pages) 0 -}}
  <ul class="home-title-list">
    {{- range $pages }}
      <li><a href="{{ .RelPermalink }}">{{ .Title }}</a></li>
    {{- end }}
  </ul>
{{- else -}}
  <p class="home-empty">{{ T $emptyKey }}</p>
{{- end -}}
```

- [ ] **Step 5: Add localized static homepage composition**

Replace the `main` block in `layouts/home.html` with:

```go-html-template
{{ define "main" }}
  {{- $projects := where .Site.RegularPages "Section" "projects" -}}
  {{- $projects = where $projects "Language.Lang" .Language.Lang -}}
  {{- $projects = where $projects "Draft" false -}}
  {{- $projects = where $projects "Params.hidden" "ne" true -}}
  {{- $pastProjects := where $projects "Params.projectstatus" "past" -}}
  {{- $pastProjects = $pastProjects.ByDate.Reverse -}}
  {{- $posts := where .Site.RegularPages "Section" "blog" -}}
  {{- $posts = where $posts "Language.Lang" .Language.Lang -}}
  {{- $posts = where $posts "Draft" false -}}
  {{- $posts = where $posts "Params.hidden" "ne" true -}}
  {{- $posts = $posts.ByDate.Reverse -}}
  <content class="home-content">
    <div class="home-intro">{{ .Content }}</div>
    <section data-home-section="projects">
      <h2>{{ T "projects" }}</h2>
      <section data-project-status="past">
        <h3>{{ T "pastProjects" }}</h3>
        {{ partial "home-title-list.html" (dict "Pages" $pastProjects "EmptyKey" "noPastProjects") }}
      </section>
    </section>
    <section data-home-section="latest">
      <h2>{{ T "latestPosts" }}</h2>
      {{ partial "home-title-list.html" (dict "Pages" (first 3 $posts) "EmptyKey" "noPosts") }}
    </section>
    <section data-home-section="popular">
      <h2>{{ T "popularPosts" }}</h2>
      <p class="home-empty">{{ T "popularUnavailable" }}</p>
    </section>
  </content>
{{ end }}
```

Keep the Task 1 `title` block above it.

- [ ] **Step 6: Add exact i18n keys**

Append to `i18n/en.toml`:

```toml
[projects]
other = "Projects"
[pastProjects]
other = "Past projects"
[noPastProjects]
other = "No past projects yet"
[latestPosts]
other = "Latest posts"
[popularPosts]
other = "Popular posts"
[popularUnavailable]
other = "Popular posts are temporarily unavailable"
```

Append to `i18n/zh.toml`:

```toml
[projects]
other = "项目"
[pastProjects]
other = "过往项目"
[noPastProjects]
other = "暂无过往项目"
[latestPosts]
other = "最新文章"
[popularPosts]
other = "热门文章"
[popularUnavailable]
other = "热门文章暂时无法加载"
```

- [ ] **Step 7: Add minimal responsive list styling**

Append to `assets/css/site.css`:

```css
.home-content > section {
  margin-block-start: 2rem;
}

.home-content [data-project-status] {
  margin-block-start: 1rem;
}

.home-title-list {
  margin-block: 0.75rem 0;
  padding-inline-start: 1.25rem;
}

.home-title-list li + li {
  margin-block-start: 0.4rem;
}

.home-empty {
  color: var(--text-color-tertiary);
}
```

- [ ] **Step 8: Run homepage and mobile-safe source tests GREEN**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_home_sections_are_ordered_title_only_and_language_local \
  tests.test_site.GeneratedSiteTests.test_home_latest_is_capped_at_three_visible_posts \
  tests.test_site.GeneratedSiteTests.test_semantic_colors_meet_text_contrast_in_both_color_schemes -v
```

Expected: all focused tests PASS.

- [ ] **Step 9: Commit the static homepage**

```bash
git add layouts/home.html layouts/_partials/home-title-list.html assets/css/site.css \
  i18n/en.toml i18n/zh.toml tests/test_site.py
git commit -m "feat: add projects and latest posts to home"
```

### Task 4: Live Count-Only Popular Post Ranking

**Files:**
- Create: `layouts/_partials/kudos-config.html`
- Create: `layouts/_partials/popular-posts.html`
- Create: `assets/js/popular-posts.mjs`
- Create: `tests/popular-posts.test.mjs`
- Modify: `layouts/_partials/kudos.html`
- Modify: `layouts/home.html`
- Modify: `i18n/en.toml`
- Modify: `i18n/zh.toml`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Write the complete ranking, request, failure, and DOM test file**

Create `tests/popular-posts.test.mjs`:

```javascript
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  loadPopularCounts,
  mountPopularPosts,
  rankPopularPosts,
} from "../assets/js/popular-posts.mjs";

function jsonResponse(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

function invalidJsonResponse(status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => { throw new SyntaxError("invalid JSON"); },
  };
}

class FakeClassList {
  constructor(...values) {
    this.values = new Set(values);
  }

  contains(value) {
    return this.values.has(value);
  }

  remove(value) {
    this.values.delete(value);
  }
}

function popularDom(entities) {
  const attributes = new Map([["aria-busy", "true"]]);
  const list = {
    hidden: true,
    children: [],
    append(element) {
      this.children = this.children.filter((candidate) => candidate !== element);
      this.children.push(element);
    },
  };
  const elements = entities.map((entity, recency) => ({
    dataset: { entity, recency: String(recency) },
    remove() {
      list.children = list.children.filter((candidate) => candidate !== this);
    },
  }));
  list.children = [...elements];
  let statusText = "Loading popular posts";
  const statusWrites = [];
  const status = {
    attributes: new Map([
      ["role", "status"],
      ["aria-live", "polite"],
      ["aria-atomic", "true"],
    ]),
    classList: new FakeClassList("visually-hidden"),
    get textContent() {
      return statusText;
    },
    set textContent(value) {
      statusText = value;
      statusWrites.push(value);
    },
    writes: statusWrites,
  };
  const root = {
    attributes,
    dataset: {
      endpoint: "https://kudos.example.test",
      popularState: "loading",
      readyLabel: "Popular posts loaded",
      timeoutMs: "5000",
      unavailableLabel: "Popular posts are temporarily unavailable",
    },
    querySelector(selector) {
      return {
        "[data-popular-list]": list,
        "[data-popular-status]": status,
      }[selector];
    },
    querySelectorAll(selector) {
      return selector === "[data-popular-candidate]" ? elements : [];
    },
    setAttribute(name, value) {
      attributes.set(name, value);
    },
  };
  return { elements, list, root, status };
}

test("initial loading and no-JavaScript states are accessible", () => {
  const dom = popularDom(["post:one", "post:two"]);
  assert.equal(dom.root.attributes.get("aria-busy"), "true");
  assert.equal(dom.list.hidden, true);
  assert.equal(dom.status.attributes.get("role"), "status");
  assert.equal(dom.status.attributes.get("aria-live"), "polite");
  assert.equal(dom.status.attributes.get("aria-atomic"), "true");
  assert.equal(dom.status.textContent, "Loading popular posts");

  const partial = readFileSync(
    new URL("../layouts/_partials/popular-posts.html", import.meta.url),
    "utf8",
  );
  assert.match(
    partial,
    /<\/div>\s*<noscript><p class="home-empty">\{\{ T "popularRequiresJavaScript" \}\}<\/p><\/noscript>/,
  );
});

test("ranks by count, breaks ties by recency, and limits to five", () => {
  const candidates = [
    { entity: "post:one", recency: 0, count: 2 },
    { entity: "post:two", recency: 1, count: 9 },
    { entity: "post:three", recency: 2, count: 9 },
    { entity: "post:four", recency: 3, count: 7 },
    { entity: "post:five", recency: 4, count: 6 },
    { entity: "post:six", recency: 5, count: 5 },
  ];
  assert.deepEqual(
    rankPopularPosts(candidates).map(({ entity }) => entity),
    ["post:two", "post:three", "post:four", "post:five", "post:six"],
  );
});

test("loads exactly one count-only request per encoded entity", async () => {
  const requests = [];
  const candidates = [
    { entity: "post:one", recency: 0 },
    { entity: "post:two", recency: 1 },
  ];
  const ranked = await loadPopularCounts({
    endpoint: "https://kudos.example.test/",
    candidates,
    fetchImpl: async (url, options) => {
      requests.push([url, options]);
      const entity = decodeURIComponent(new URL(url).pathname.slice(1));
      return jsonResponse({ entity, count: entity.endsWith("two") ? 2 : 1 });
    },
    timeoutMs: 5000,
  });
  assert.deepEqual(ranked.map(({ entity }) => entity), ["post:two", "post:one"]);
  assert.deepEqual(requests.map(([url]) => new URL(url).pathname), [
    "/post%3Aone",
    "/post%3Atwo",
  ]);
  for (const [url, options] of requests) {
    assert.equal(new URL(url).pathname.endsWith("/kudos"), false);
    assert.equal(options.credentials, "omit");
    assert.equal(options.referrerPolicy, "no-referrer");
    assert.ok(options.signal instanceof AbortSignal);
  }
});

test("zero or one candidate never performs a ranking request", async () => {
  for (const candidates of [
    [],
    [{ entity: "post:only", recency: 0 }],
  ]) {
    let requests = 0;
    const result = await loadPopularCounts({
      endpoint: "https://kudos.example.test",
      candidates,
      fetchImpl: async () => {
        requests += 1;
        throw new Error("must not fetch");
      },
    });
    assert.equal(requests, 0);
    assert.deepEqual(result, candidates);
  }
});

test("rejects malformed successful count payloads", async (context) => {
  const invalidPayloads = [
    null,
    [],
    {},
    { entity: "post:other", count: 1 },
    { entity: "post:one" },
    { entity: "post:one", count: -1 },
    { entity: "post:one", count: 1.5 },
    { entity: "post:one", count: Number.MAX_SAFE_INTEGER + 1 },
    { entity: "post:one", count: "1" },
  ];
  for (const payload of invalidPayloads) {
    await context.test(JSON.stringify(payload), async () => {
      await assert.rejects(loadPopularCounts({
        endpoint: "https://kudos.example.test",
        candidates: [
          { entity: "post:one", recency: 0 },
          { entity: "post:two", recency: 1 },
        ],
        fetchImpl: async (url) => (
          url.endsWith("post%3Aone")
            ? jsonResponse(payload)
            : jsonResponse({ entity: "post:two", count: 2 })
        ),
      }));
    });
  }
});

test("rejects invalid JSON and non-success responses", async () => {
  const candidates = [
    { entity: "post:one", recency: 0 },
    { entity: "post:two", recency: 1 },
  ];
  await assert.rejects(loadPopularCounts({
    endpoint: "https://kudos.example.test",
    candidates,
    fetchImpl: async () => invalidJsonResponse(),
  }), /invalid JSON/);
  await assert.rejects(loadPopularCounts({
    endpoint: "https://kudos.example.test",
    candidates,
    fetchImpl: async () => jsonResponse({ error: "offline" }, 503),
  }), /503/);
});

test("a shared timeout aborts the complete ranking", async () => {
  const candidates = [
    { entity: "post:one", recency: 0 },
    { entity: "post:two", recency: 1 },
  ];
  await assert.rejects(loadPopularCounts({
    endpoint: "https://kudos.example.test",
    candidates,
    timeoutMs: 1,
    fetchImpl: async (url, options) => new Promise((resolve, reject) => {
      options.signal.addEventListener("abort", () => reject(new Error("aborted")));
    }),
  }), /aborted/);
});

test("one failed count prevents a partial ranking", async () => {
  const candidates = [
    { entity: "post:one", recency: 0 },
    { entity: "post:two", recency: 1 },
  ];
  await assert.rejects(loadPopularCounts({
    endpoint: "https://kudos.example.test",
    candidates,
    fetchImpl: async (url) => (
      url.endsWith("post%3Aone")
        ? jsonResponse({ entity: "post:one", count: 99 })
        : jsonResponse({ error: "offline" }, 503)
    ),
  }), /503/);
});

test("the first failed count aborts every pending sibling request", async () => {
  let siblingAborted = false;
  const candidates = [
    { entity: "post:one", recency: 0 },
    { entity: "post:two", recency: 1 },
  ];
  await assert.rejects(loadPopularCounts({
    endpoint: "https://kudos.example.test",
    candidates,
    fetchImpl: async (url, options) => {
      if (url.endsWith("post%3Aone")) {
        return jsonResponse({ error: "offline" }, 503);
      }
      return new Promise((resolve, reject) => {
        options.signal.addEventListener("abort", () => {
          siblingAborted = true;
          reject(new Error("sibling aborted"));
        });
      });
    },
  }), /503/);
  assert.equal(siblingAborted, true);
});

test("reveals only the final five ordered links after every count succeeds", async () => {
  const dom = popularDom([
    "post:one", "post:two", "post:three",
    "post:four", "post:five", "post:six",
  ]);
  const controller = mountPopularPosts(dom.root, async (url) => {
    const entity = decodeURIComponent(new URL(url).pathname.slice(1));
    const counts = {
      "post:one": 1,
      "post:two": 6,
      "post:three": 5,
      "post:four": 4,
      "post:five": 3,
      "post:six": 2,
    };
    return jsonResponse({ entity, count: counts[entity] });
  }, { error() {} });
  await controller.ready;
  assert.equal(dom.list.hidden, false);
  assert.deepEqual(dom.list.children.map(({ dataset }) => dataset.entity), [
    "post:two", "post:three", "post:four", "post:five", "post:six",
  ]);
  assert.equal(dom.root.attributes.get("aria-busy"), "false");
  assert.equal(dom.root.dataset.popularState, "ready");
  assert.equal(dom.status.textContent, "Popular posts loaded");
  assert.deepEqual(dom.status.writes, ["Popular posts loaded"]);
});

test("contains failure, keeps candidates hidden, and announces it once", async () => {
  const dom = popularDom(["post:one", "post:two"]);
  const errors = [];
  const controller = mountPopularPosts(
    dom.root,
    async () => { throw new Error("offline"); },
    { error(...values) { errors.push(values); } },
  );
  await assert.doesNotReject(controller.ready);
  assert.equal(dom.list.hidden, true);
  assert.equal(dom.status.textContent, "Popular posts are temporarily unavailable");
  assert.deepEqual(dom.status.writes, ["Popular posts are temporarily unavailable"]);
  assert.equal(dom.status.classList.contains("visually-hidden"), false);
  assert.equal(dom.root.attributes.get("aria-busy"), "false");
  assert.equal(dom.root.dataset.popularState, "error");
  assert.equal(errors.length, 1);
});
```

- [ ] **Step 2: Run the new file once to confirm its syntax reaches the missing module**

Run:

```bash
node --test tests/popular-posts.test.mjs
```

Expected: FAIL only with `ERR_MODULE_NOT_FOUND`; there must be no syntax error in the test file.

- [ ] **Step 3: Record the TDD RED result**

Run:

```bash
node --test tests/popular-posts.test.mjs
```

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `assets/js/popular-posts.mjs`.

- [ ] **Step 4: Implement the count-only module**

Create `assets/js/popular-posts.mjs`:

```javascript
function requireCount(data, entity) {
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("Kudos returned an invalid payload");
  }
  if (data.entity !== entity) throw new Error("Kudos returned the wrong entity");
  if (!Number.isSafeInteger(data.count) || data.count < 0) {
    throw new Error("Kudos returned an invalid count");
  }
  return data.count;
}

export function rankPopularPosts(candidates, limit = 5) {
  return [...candidates]
    .sort((left, right) => right.count - left.count || left.recency - right.recency)
    .slice(0, limit);
}

export async function loadPopularCounts({
  endpoint,
  candidates,
  fetchImpl = globalThis.fetch,
  timeoutMs = 5000,
}) {
  if (candidates.length < 2) return [...candidates];
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const counted = await Promise.all(candidates.map(async (candidate) => {
      const root = endpoint.replace(/\/+$/, "");
      const response = await fetchImpl(
        `${root}/${encodeURIComponent(candidate.entity)}`,
        {
          credentials: "omit",
          referrerPolicy: "no-referrer",
          signal: controller.signal,
        },
      );
      let data;
      try {
        data = await response.json();
      } catch {
        throw new Error(`Kudos returned invalid JSON (${response.status})`);
      }
      if (!response.ok) throw new Error(`Kudos request failed (${response.status})`);
      return { ...candidate, count: requireCount(data, candidate.entity) };
    }));
    return rankPopularPosts(counted);
  } catch (error) {
    controller.abort();
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function mountPopularPosts(root, fetchImpl = globalThis.fetch, logger = console) {
  const list = root.querySelector("[data-popular-list]");
  const status = root.querySelector("[data-popular-status]");
  const elements = [...root.querySelectorAll("[data-popular-candidate]")];
  const candidates = elements.map((element) => ({
    element,
    entity: element.dataset.entity,
    recency: Number.parseInt(element.dataset.recency, 10),
  }));

  async function load() {
    try {
      const ranked = await loadPopularCounts({
        endpoint: root.dataset.endpoint,
        candidates,
        fetchImpl,
        timeoutMs: Number.parseInt(root.dataset.timeoutMs, 10),
      });
      const selected = new Set(ranked.map(({ element }) => element));
      for (const element of elements) {
        if (!selected.has(element)) element.remove();
      }
      for (const { element } of ranked) list.append(element);
      list.hidden = false;
      status.textContent = root.dataset.readyLabel;
      root.dataset.popularState = "ready";
    } catch (error) {
      status.textContent = root.dataset.unavailableLabel;
      status.classList.remove("visually-hidden");
      root.dataset.popularState = "error";
      logger.error("Failed to load popular posts", error);
    } finally {
      root.setAttribute("aria-busy", "false");
    }
  }

  return { ready: load() };
}

function mountAll() {
  for (const root of document.querySelectorAll("[data-popular-posts]")) {
    mountPopularPosts(root);
  }
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll, { once: true });
  } else {
    mountAll();
  }
}
```

- [ ] **Step 5: Extract the existing strict Kudos configuration guard**

Create `layouts/_partials/kudos-config.html`:

```go-html-template
{{- $page := . -}}
{{- $kudos := dict -}}
{{- if isset $page.Site.Params "kudos" -}}
  {{- $configured := index $page.Site.Params "kudos" -}}
  {{- if reflect.IsMap $configured }}{{ $kudos = $configured }}{{ end -}}
{{- end -}}

{{- $enabled := false -}}
{{- if isset $kudos "enabled" -}}
  {{- $value := index $kudos "enabled" -}}
  {{- if eq (printf "%T" $value) "bool" }}{{ $enabled = $value }}{{ end -}}
{{- end -}}

{{- $endpoint := "" -}}
{{- if isset $kudos "endpoint" -}}
  {{- $value := index $kudos "endpoint" -}}
  {{- if eq (printf "%T" $value) "string" -}}
    {{- $endpoint = strings.TrimSpace $value -}}
  {{- end -}}
{{- end -}}

{{- $httpsPattern := `^https://([A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)(\.([A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?))*(:[0-9]{1,5})?/?$` -}}
{{- $loopbackPattern := `^http://(127\.0\.0\.1|localhost)(:[0-9]{1,5})?/?$` -}}
{{- $validHTTPS := gt (len (findRE $httpsPattern $endpoint)) 0 -}}
{{- $validLoopback := gt (len (findRE $loopbackPattern $endpoint)) 0 -}}
{{- $validPort := true -}}
{{- if gt (len (findRE `:[0-9]{1,5}/?$` $endpoint)) 0 -}}
  {{- $port := int (replaceRE `^.*:([0-9]{1,5})/?$` "$1" $endpoint) -}}
  {{- $validPort = and (ge $port 1) (le $port 65535) -}}
{{- end -}}

{{- return (dict
  "enabled" (and $enabled $validPort (or $validHTTPS $validLoopback))
  "endpoint" $endpoint
) -}}
```

Replace `layouts/_partials/kudos.html` with:

```go-html-template
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/_default/single.html; site-local Kudos integration. */ -}}
{{- $page := .Page -}}
{{- $entity := .Entity -}}
{{- $config := partial "kudos-config.html" $page -}}
{{- if and $entity $config.enabled -}}
  <div class="upvote-container post-interaction" data-kudos
    data-kudos-entity="{{ $entity }}" data-kudos-endpoint="{{ $config.endpoint }}"
    data-add-label="{{ T "upvoteAdd" }}" data-remove-label="{{ T "upvoteRemove" }}"
    data-loading-label="{{ T "upvoteLoading" }}"
    data-unavailable-label="{{ T "upvoteUnavailable" }}"
    data-update-failed-label="{{ T "upvoteUpdateFailed" }}"
    data-kudos-state="loading" aria-busy="true" hidden>
    <small class="upvote">
      <button class="upvote-btn" type="button" data-kudos-button aria-label="{{ T "upvoteLoading" }}" disabled>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <polyline points="17 11 12 6 7 11"></polyline>
          <polyline points="17 18 12 13 7 18"></polyline>
        </svg>
        <span class="upvote-count" data-kudos-count aria-live="polite">—</span>
      </button>
      <span class="visually-hidden" data-kudos-status role="status">{{ T "upvoteLoading" }}</span>
    </small>
  </div>
  {{- $script := resources.Get "js/kudos.mjs" | fingerprint "sha256" -}}
  <script type="module" src="{{ $script.RelPermalink }}" integrity="{{ $script.Data.Integrity }}"></script>
{{- end -}}
```

- [ ] **Step 6: Add the guarded popular-post partial**

Create `layouts/_partials/popular-posts.html`:

```go-html-template
{{- $page := . -}}
{{- $posts := where $page.Site.RegularPages "Section" "blog" -}}
{{- $posts = where $posts "Language.Lang" $page.Language.Lang -}}
{{- $posts = where $posts "Draft" false -}}
{{- $posts = where $posts "Params.hidden" "ne" true -}}
{{- $posts = $posts.ByDate.Reverse -}}
{{- $count := len $posts -}}
<section data-home-section="popular">
  <h2>{{ T "popularPosts" }}</h2>
  {{- if eq $count 0 }}
    <p class="home-empty">{{ T "noPosts" }}</p>
  {{- else if eq $count 1 }}
    {{ partial "home-title-list.html" (dict "Pages" $posts "EmptyKey" "noPosts") }}
  {{- else }}
    {{- $config := partial "kudos-config.html" $page -}}
    {{- if $config.enabled }}
      <div data-popular-posts data-endpoint="{{ $config.endpoint }}"
        data-timeout-ms="5000" data-popular-state="loading"
        data-ready-label="{{ T "popularReady" }}"
        data-unavailable-label="{{ T "popularUnavailable" }}"
        aria-busy="true">
        <p class="visually-hidden" data-popular-status role="status"
          aria-live="polite" aria-atomic="true">{{ T "popularLoading" }}</p>
        <ol class="home-title-list" data-popular-list hidden>
          {{- range $index, $post := $posts }}
            {{- $entity := partial "interaction-id.html" $post -}}
            <li data-popular-candidate data-entity="{{ $entity }}"
              data-recency="{{ $index }}"><a href="{{ $post.RelPermalink }}">{{ $post.Title }}</a></li>
          {{- end }}
        </ol>
      </div>
      <noscript><p class="home-empty">{{ T "popularRequiresJavaScript" }}</p></noscript>
      {{- $script := resources.Get "js/popular-posts.mjs" | fingerprint "sha256" }}
      <script type="module" src="{{ $script.RelPermalink }}" integrity="{{ $script.Data.Integrity }}"></script>
    {{- else }}
      <p class="home-empty">{{ T "popularUnavailable" }}</p>
    {{- end }}
  {{- end }}
</section>
```

Replace the temporary popular `<section>` in `layouts/home.html` with:

```go-html-template
{{ partial "popular-posts.html" . }}
```

- [ ] **Step 7: Add exact localized runtime states**

Append to `i18n/en.toml`:

```toml
[popularLoading]
other = "Loading popular posts"
[popularReady]
other = "Popular posts loaded"
[popularRequiresJavaScript]
other = "Enable JavaScript to load popular posts"
```

Append to `i18n/zh.toml`:

```toml
[popularLoading]
other = "正在加载热门文章"
[popularReady]
other = "热门文章已加载"
[popularRequiresJavaScript]
other = "请启用 JavaScript 以加载热门文章"
```

- [ ] **Step 8: Add generated-markup and SRI tests**

Add this test to `tests/test_site.py`:

```python
def test_popular_posts_emit_language_local_count_only_candidates(self):
    module_pattern = re.compile(
        r'<script(?=[^>]*type="module")(?=[^>]*src="([^"]*popular-posts[^"]*)")'
        r'(?=[^>]*integrity="([^"]+)")[^>]*></script>'
    )
    with TemporaryDirectory() as temporary:
        for name, base_url, base_path in (
            ("root", "https://example.test/", "/"),
            ("project", "https://example.test/example-blog/", "/example-blog/"),
        ):
            public = Path(temporary) / name
            build_site(public, base_url)
            english = read_html(public, "index.html")
            chinese = read_html(public, "zh/index.html")
            popular = re.search(
                r'<section data-home-section="popular">(.*?)</section>',
                english,
                re.DOTALL,
            ).group(1)
            self.assertEqual(
                ["post:lekythos-a-shape", "post:the-miracle-of-istanbul"],
                re.findall(r'data-entity="([^"]+)"', popular),
            )
            self.assertEqual(["0", "1"], re.findall(r'data-recency="([0-9]+)"', popular))
            self.assertNotIn("post:beyond-the-cloud", popular)
            self.assertIn(f'href="{base_path}p/lekythos-a-shape/"', popular)
            self.assertIn(
                f'href="{base_path}p/the-miracle-of-istanbul/"', popular
            )
            self.assertNotIn("data-kudos-count", popular)
            self.assertIn("data-popular-list hidden", popular)
            self.assertIn('aria-busy="true"', popular)
            self.assertIn('role="status"', popular)
            self.assertEqual(1, popular.count("data-popular-status"))
            self.assertRegex(
                popular,
                r'<p[^>]*data-popular-status[^>]*role="status"'
                r'[^>]*aria-live="polite"[^>]*aria-atomic="true"[^>]*>'
                r'Loading popular posts</p>',
            )
            self.assertRegex(
                popular,
                r'</div>\s*<noscript><p class="home-empty">'
                r'Enable JavaScript to load popular posts</p></noscript>',
            )
            modules = module_pattern.findall(english)
            self.assertEqual(1, len(modules))
            source, integrity = modules[0]
            self.assertTrue(source.startswith(f"{base_path}js/popular-posts."), source)
            asset = public / urlsplit(source).path.removeprefix(base_path)
            self.assertTrue(asset.is_file(), source)
            expected_integrity = "sha256-" + base64.b64encode(
                hashlib.sha256(asset.read_bytes()).digest()
            ).decode("ascii")
            self.assertEqual(expected_integrity, integrity)

            self.assertIn("暂无文章", chinese)
            self.assertNotIn("data-popular-candidate", chinese)
            self.assertEqual([], module_pattern.findall(chinese))

        for index, config in enumerate((
            "disabled-kudos.toml",
            "invalid-kudos-container-scalar.toml",
            "invalid-endpoint-relative.toml",
        )):
            public = Path(temporary) / f"invalid-{index}"
            build_site(
                public,
                "https://example.test/",
                "--config",
                f"hugo.toml,tests/fixtures/{config}",
            )
            home = read_html(public, "index.html")
            self.assertNotIn("data-popular-posts", home)
            self.assertEqual([], module_pattern.findall(home))
            self.assertIn("Popular posts are temporarily unavailable", home)
```

Add a language-local hidden-candidate and localized-fallback regression:

```python
def test_popular_candidates_exclude_hidden_posts_in_each_language(self):
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        content = temporary_root / "content"
        content.mkdir()
        (content / "_index.en.md").write_text(
            '+++\ntitle = "Where Was I"\n+++\n\nHome.\n', encoding="utf-8"
        )
        (content / "_index.zh.md").write_text(
            '+++\ntitle = "说哪儿了"\n+++\n\n首页。\n', encoding="utf-8"
        )
        for ordinal in (1, 2):
            bundle = content / "blog" / f"visible-{ordinal}"
            bundle.mkdir(parents=True)
            for language, title in (
                ("en", f"Visible {ordinal}"),
                ("zh", f"可见文章 {ordinal}"),
            ):
                (bundle / f"index.{language}.md").write_text(
                    "+++\n"
                    f'title = "{title}"\n'
                    f"date = 2026-08-0{ordinal}\n"
                    "draft = false\n"
                    f'interactionId = "visible-{ordinal}"\n'
                    "+++\n\nBody.\n",
                    encoding="utf-8",
                )
        hidden = content / "blog/hidden-popular"
        hidden.mkdir(parents=True)
        for language, title in (("en", "Hidden"), ("zh", "隐藏文章")):
            (hidden / f"index.{language}.md").write_text(
                "+++\n"
                f'title = "{title}"\n'
                "date = 2026-08-03\n"
                "draft = false\n"
                "hidden = true\n"
                'interactionId = "hidden-popular"\n'
                "+++\n\nHidden.\n",
                encoding="utf-8",
            )
        draft = content / "blog/draft-popular"
        draft.mkdir(parents=True)
        for language, title in (("en", "Draft"), ("zh", "草稿文章")):
            (draft / f"index.{language}.md").write_text(
                "+++\n"
                f'title = "{title}"\n'
                "date = 2026-08-03\n"
                "draft = true\n"
                'interactionId = "draft-popular"\n'
                "+++\n\nDraft.\n",
                encoding="utf-8",
            )

        for name, base_url, base_path in (
            ("root", "https://example.test/", "/"),
            ("project", "https://example.test/example-blog/", "/example-blog/"),
        ):
            public = temporary_root / name
            build_site(
                public,
                base_url,
                "--contentDir",
                str(content),
                "--buildDrafts",
            )
            for language, relative, language_path, noscript_label in (
                (
                    "en",
                    "index.html",
                    "",
                    "Enable JavaScript to load popular posts",
                ),
                (
                    "zh",
                    "zh/index.html",
                    "zh/",
                    "请启用 JavaScript 以加载热门文章",
                ),
            ):
                with self.subTest(build=name, language=language):
                    html = read_html(public, relative)
                    popular = re.search(
                        r'<section data-home-section="popular">(.*?)</section>',
                        html,
                        re.DOTALL,
                    ).group(1)
                    self.assertEqual(
                        ["post:visible-2", "post:visible-1"],
                        re.findall(r'data-entity="([^"]+)"', popular),
                    )
                    self.assertIn(
                        f'href="{base_path}{language_path}p/visible-2/"',
                        popular,
                    )
                    self.assertNotIn("post:hidden-popular", popular)
                    self.assertNotIn("post:draft-popular", popular)
                    self.assertEqual(1, popular.count("data-popular-status"))
                    self.assertIn(
                        f'<noscript><p class="home-empty">{noscript_label}</p></noscript>',
                        popular,
                    )
```

Add the zero/one generated-template proof:

```python
def test_popular_posts_do_not_load_ranking_for_zero_or_one_candidate(self):
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        content = temporary_root / "content"
        bundle = content / "blog/only-post"
        bundle.mkdir(parents=True)
        (content / "_index.en.md").write_text(
            '+++\ntitle = "Where Was I"\n+++\n\nHome.\n', encoding="utf-8"
        )
        (content / "_index.zh.md").write_text(
            '+++\ntitle = "说哪儿了"\n+++\n\n首页。\n', encoding="utf-8"
        )
        (bundle / "index.en.md").write_text(
            '+++\ntitle = "Only post"\ndate = 2026-08-09\ndraft = false\n'
            'interactionId = "only-post"\n+++\n\nBody.\n',
            encoding="utf-8",
        )
        for name, base_url, base_path in (
            ("root", "https://example.test/", "/"),
            ("project", "https://example.test/example-blog/", "/example-blog/"),
        ):
            public = temporary_root / name
            build_site(public, base_url, "--contentDir", str(content))
            english = read_html(public, "index.html")
            chinese = read_html(public, "zh/index.html")
            popular = re.search(
                r'<section data-home-section="popular">(.*?)</section>',
                english,
                re.DOTALL,
            ).group(1)
            self.assertIn(">Only post</a>", popular)
            self.assertIn(f'href="{base_path}p/only-post/"', popular)
            for html in (english, chinese):
                self.assertNotIn("data-popular-posts", html)
                self.assertNotIn("data-popular-candidate", html)
                self.assertNotIn("js/popular-posts.", html)
```

- [ ] **Step 9: Run the full popular/Kudos slice GREEN**

Run:

```bash
node --test tests/popular-posts.test.mjs tests/kudos.test.mjs
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_popular_posts_emit_language_local_count_only_candidates \
  tests.test_site.GeneratedSiteTests.test_popular_candidates_exclude_hidden_posts_in_each_language \
  tests.test_site.GeneratedSiteTests.test_popular_posts_do_not_load_ranking_for_zero_or_one_candidate \
  tests.test_site.GeneratedSiteTests.test_kudos_endpoint_configuration_is_strict_and_graceful \
  tests.test_site.GeneratedSiteTests.test_kudos_uses_shared_entities_accessible_ssr_and_hashed_modules -v
node --check assets/js/popular-posts.mjs
```

Expected: all Node and Python tests PASS; the article Kudos behavior remains unchanged.

- [ ] **Step 10: Commit live popularity**

```bash
git add assets/js/popular-posts.mjs layouts/_partials/kudos-config.html \
  layouts/_partials/kudos.html layouts/_partials/popular-posts.html layouts/home.html \
  i18n/en.toml i18n/zh.toml tests/popular-posts.test.mjs tests/test_site.py
git commit -m "feat: rank popular posts from live Kudos counts"
```

### Task 5: Project-First Tag Results

**Files:**
- Create: `tests/fixtures/content/projects/_index.en.md`
- Create: `tests/fixtures/content/projects/_index.zh.md`
- Create: `tests/fixtures/content/projects/shared-project/index.en.md`
- Create: `tests/fixtures/content/projects/shared-project/index.zh.md`
- Create: `tests/fixtures/content/projects/older-project/index.en.md`
- Modify: `layouts/_partials/post-list.html`
- Modify: `layouts/term.html`
- Modify: `i18n/en.toml`
- Modify: `i18n/zh.toml`
- Modify: `tests/post-search.test.mjs`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Add a bilingual tagged project fixture**

Create `tests/fixtures/content/projects/_index.en.md`:

```markdown
+++
title = "Projects"
[build]
  render = "never"
+++
```

Create `tests/fixtures/content/projects/_index.zh.md`:

```markdown
+++
title = "项目"
[build]
  render = "never"
+++
```

Create `tests/fixtures/content/projects/shared-project/index.en.md`:

```markdown
+++
title = "Shared project"
date = 2026-08-09
lastmod = 2026-08-09
draft = false
tags = ["fixture"]
interactionId = "shared-project"
projectStatus = "past"
+++

English project fixture.
```

Create `tests/fixtures/content/projects/shared-project/index.zh.md`:

```markdown
+++
title = "共享项目"
date = 2026-08-09
lastmod = 2026-08-09
draft = false
tags = ["测试"]
interactionId = "shared-project"
projectStatus = "past"
+++

中文项目测试内容。
```

Create `tests/fixtures/content/projects/older-project/index.en.md` without a
Chinese sibling:

```markdown
+++
title = "Older project"
date = 2026-08-07
lastmod = 2026-08-07
draft = false
tags = ["fixture"]
interactionId = "older-project"
projectStatus = "past"
+++

English-only project fixture.
```

- [ ] **Step 2: Write the failing group-order and combined-count test**

Add:

```python
def test_tag_results_group_projects_before_posts(self):
    with TemporaryDirectory() as temporary:
        for name, base_url, base_path in (
            ("root", "https://example.test/", "/"),
            ("project", "https://example.test/example-blog/", "/example-blog/"),
        ):
            public = Path(temporary) / name
            build_site(
                public,
                base_url,
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            english = read_html(public, "tags/fixture/index.html")
            chinese = read_html(public, "zh/tags/测试/index.html")
            english_home = read_html(public, "index.html")
            chinese_home = read_html(public, "zh/index.html")
            self.assertIn("Shared project", english_home)
            self.assertIn("Older project", english_home)
            self.assertIn("共享项目", chinese_home)
            self.assertNotIn("共享项目", english_home)
            self.assertNotIn("Shared project", chinese_home)
            self.assertNotIn("Older project", chinese_home)
            self.assertLess(english.index(">Projects</h3>"), english.index(">Posts</h3>"))
            self.assertLess(english.index("Shared project"), english.index("Shared article"))
            self.assertLess(chinese.index(">项目</h3>"), chinese.index(">文章</h3>"))
            self.assertLess(chinese.index("共享项目"), chinese.index("共享文章"))

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

            self.assertIn("2 projects", english_projects)
            self.assertIn("Shared project", english_projects)
            self.assertIn("Older project", english_projects)
            self.assertNotIn("Shared article", english_projects)
            self.assertIn('placeholder="Search projects"', english_projects)
            self.assertIn("No matching projects", english_projects)
            self.assertEqual(1, english_projects.count("data-post-search"))
            self.assertIn("1 post", english_posts)
            self.assertIn("Shared article", english_posts)
            self.assertNotIn("Shared project", english_posts)
            self.assertNotIn("Older project", english_posts)
            self.assertEqual(0, english_posts.count("data-post-search"))
            self.assertIn("1 个项目", chinese_projects)
            self.assertIn("共享项目", chinese_projects)
            self.assertNotIn("共享文章", chinese_projects)
            self.assertEqual(0, chinese_projects.count("data-post-search"))
            self.assertIn("2 篇文章", chinese_posts)
            self.assertIn("共享文章", chinese_posts)
            self.assertIn("仅中文文章", chinese_posts)
            self.assertNotIn("共享项目", chinese_posts)
            self.assertIn('placeholder="搜索文章"', chinese_posts)
            self.assertEqual(1, chinese_posts.count("data-post-search"))
            self.assertEqual(1, english.count("js/post-search."))
            self.assertEqual(1, chinese.count("js/post-search."))

            for path in (
                "p/shared-project/",
                "p/older-project/",
                "p/shared-article/",
            ):
                self.assertIn(f'href="{base_path}{path}"', english)
            self.assertIn(f'href="{base_path}zh/p/shared-project/"', chinese)
            self.assertIn(f'href="{base_path}zh/p/shared-article/"', chinese)
            overview = read_html(public, "tags/index.html")
            chinese_overview = read_html(public, "zh/tags/index.html")
            self.assertRegex(overview, r"#fixture</a><span[^>]*>3</span>")
            self.assertRegex(chinese_overview, r"#测试</a><span[^>]*>3</span>")

            production = Path(temporary) / f"{name}-production"
            build_site(production, base_url)
            visualization = read_html(
                production, "tags/visualization/index.html"
            )
            self.assertIn(">Projects</h3>", visualization)
            self.assertIn("Beyond the Cloud", visualization)
            self.assertIn(
                f'href="{base_path}p/beyond-the-cloud/"', visualization
            )
            self.assertNotIn('data-tag-group="posts"', visualization)
            self.assertNotIn("data-post-search", visualization)
            self.assertNotIn("js/post-search.", visualization)
```

- [ ] **Step 3: Run the focused tag test and observe RED**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_tag_results_group_projects_before_posts -v
```

Expected: FAIL because the term template renders one undifferentiated post list.

- [ ] **Step 4: Parameterize visible list labels without changing defaults**

Replace `layouts/_partials/post-list.html` with:

```go-html-template
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/_default/list.html */ -}}
{{ $page := .Page }}
{{ $countKey := default "postCount" .CountKey }}
{{ $searchKey := default "searchPosts" .SearchKey }}
{{ $emptyKey := default "noPosts" .EmptyKey }}
{{ $searchEmptyKey := default "noSearchResults" .SearchEmptyKey }}
{{ $searchMinimum := default 1 .SearchMinimum }}
{{ $pages := (where .Pages "Params.hidden" "ne" true).ByDate.Reverse }}
{{ $count := len $pages }}
<section class="post-list" data-post-list
  data-count-one="{{ replace (T $countKey 1) "1" "{count}" }}"
  data-count-many="{{ replace (T $countKey 2) "2" "{count}" }}">
  {{ if and $page.Site.Params.postSearch (ge $count $searchMinimum) }}
    <label>
      <span class="visually-hidden">{{ T $searchKey }}</span>
      <input type="search" data-post-search placeholder="{{ T $searchKey }}" autocomplete="off">
    </label>
  {{ end }}
  {{ if $page.Site.Params.showPostCount }}
    <p data-post-count>{{ T $countKey $count }}</p>
  {{ end }}
  <p data-search-empty hidden>{{ T $searchEmptyKey }}</p>
  <p class="visually-hidden" data-search-status role="status" aria-live="polite" aria-atomic="true"></p>
  <ul class="blog-posts">
    {{ range $pages.GroupByDate "2006" }}
      {{ if $page.Site.Params.groupByYear }}<li class="post-year" data-post-year="{{ .Key }}"><strong>{{ .Key }}</strong></li>{{ end }}
      {{ range .Pages }}
        <li data-post-item data-post-year="{{ .Date.Year }}" data-post-title="{{ .Title }}">
          <span class="{{ if $page.Site.Params.groupByYear }}grouped{{ else }}ungrouped{{ end }}">
            <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date | time.Format $page.Site.Params.dateFormat }}</time>
          </span>
          <a href="{{ .RelPermalink }}">{{ .Title }}</a>
        </li>
      {{ end }}
    {{ else }}
      <li data-empty-state>{{ T $emptyKey }}</li>
    {{ end }}
  </ul>
</section>
{{ if and $page.Site.Params.postSearch (ge $count $searchMinimum) }}
  {{ $search := resources.Get "js/post-search.mjs" | fingerprint }}
  <script type="module" src="{{ $search.RelPermalink }}" integrity="{{ $search.Data.Integrity }}"></script>
{{ end }}
```

The default blog/archive caller supplies no override keys, so its existing
one-item search threshold, visible labels, and DOM contract remain unchanged.
Term-group callers set `SearchMinimum` to `2`, where filtering can change that
group's result set.

- [ ] **Step 5: Split tag pages by visible section**

Replace `layouts/term.html` with:

```go-html-template
{{- /* Site-local Hugo 0.164 term template. */ -}}
{{ define "main" }}
  <content>
    <h2>{{ T "filteringFor" .Title }}</h2>
    {{ with .Site.GetPage "/tags" }}<p><a href="{{ .RelPermalink }}">{{ T "allTags" }}</a></p>{{ end }}
    {{- $visible := where .Pages "Params.hidden" "ne" true -}}
    {{- $projects := where $visible "Section" "projects" -}}
    {{- $posts := where $visible "Section" "blog" -}}
    {{- if gt (len $projects) 0 }}
      <section data-tag-group="projects">
        <h3>{{ T "projects" }}</h3>
        {{ partial "post-list.html" (dict
          "Page" . "Pages" $projects
          "CountKey" "projectCount" "SearchKey" "searchProjects"
          "SearchEmptyKey" "noProjectSearchResults"
          "SearchMinimum" 2
        ) }}
      </section>
    {{- end }}
    {{- if gt (len $posts) 0 }}
      <section data-tag-group="posts">
        <h3>{{ T "posts" }}</h3>
        {{ partial "post-list.html" (dict
          "Page" . "Pages" $posts "SearchMinimum" 2
        ) }}
      </section>
    {{- end }}
    {{- if and (eq (len $projects) 0) (eq (len $posts) 0) }}
      <p>{{ T "noTaggedContent" }}</p>
    {{- end }}
  </content>
{{ end }}
```

- [ ] **Step 6: Add tag/group localization**

Change English `filteringFor` to `Tagged “{{ . }}”` and Chinese to `标签“{{ . }}”下的内容`. Add:

```toml
# en
[posts]
other = "Posts"
[searchProjects]
other = "Search projects"
[projectCount]
one = "{{ . }} project"
other = "{{ . }} projects"
[noProjectSearchResults]
other = "No matching projects"
[noTaggedContent]
other = "No tagged content yet"
```

```toml
# zh
[posts]
other = "文章"
[searchProjects]
other = "搜索项目"
[projectCount]
one = "{{ . }} 个项目"
other = "{{ . }} 个项目"
[noProjectSearchResults]
other = "没有匹配的项目"
[noTaggedContent]
other = "暂无相关内容"
```

Append this independent-group regression to `tests/post-search.test.mjs`:

```javascript
test("project and post groups filter independently", () => {
  const projects = createPostList();
  const posts = createPostList();
  projects.root.dataset.countOne = "{count} project";
  projects.root.dataset.countMany = "{count} projects";
  projects.count.textContent = "2 projects";
  mountPostSearch(projects.root);
  mountPostSearch(posts.root);

  projects.input.value = "newer";
  projects.input.dispatch("input");

  assert.equal(projects.count.textContent, "1 project");
  assert.deepEqual(projects.items.map((item) => item.hidden), [false, true]);
  assert.equal(posts.count.textContent, "2 posts");
  assert.deepEqual(posts.items.map((item) => item.hidden), [false, false]);
});
```

- [ ] **Step 7: Run tag, search, taxonomy, and sitemap regressions**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_tag_results_group_projects_before_posts \
  tests.test_site.GeneratedSiteTests.test_initial_chinese_lists_are_valid_and_empty \
  tests.test_site.GeneratedSiteTests.test_root_and_project_subpath_production_matrix_is_complete -v
node --test tests/post-search.test.mjs
```

Expected: all focused tests PASS. In fixture assertions, `fixture` has three
English pages (`Shared project`, `Older project`, `Shared article`) and `测试`
has three Chinese pages (`共享项目`, `共享文章`, `仅中文文章`). The missing Chinese
translation for `Older project` never falls back into Chinese output.
`same-spelling` remains one independent page per language and term pages still
emit no hreflang links merely because the term spelling matches.

- [ ] **Step 8: Commit tag grouping**

```bash
git add tests/fixtures/content/projects layouts/_partials/post-list.html layouts/term.html \
  i18n/en.toml i18n/zh.toml tests/post-search.test.mjs tests/test_site.py
git commit -m "feat: group tagged projects before posts"
```

### Task 6: Documentation, Full Acceptance, and Deployment Readiness

**Files:**
- Modify: `README.md`
- Modify: `tests/test_repository.py`

- [ ] **Step 1: Write failing documentation-contract assertions**

In `tests/test_repository.py`, add assertions that README contains all of:

```python
for phrase in (
    "Where Was I",
    "content/projects/",
    "--section projects",
    "Popular posts",
    "count-only",
    "http://localhost:1313",
):
    self.assertIn(phrase, readme)
self.assertNotIn(
    "Hugo publishes only resources copied into `content/blog/` leaf bundles.",
    readme,
)
```

- [ ] **Step 2: Run the documentation test and observe RED**

Run:

```bash
python3 -m unittest tests.test_repository -v
```

Expected: FAIL because README does not yet describe projects or homepage count requests.

- [ ] **Step 3: Reconcile README with the implemented site**

Replace the README heading:

```markdown
# Where Was I / 说哪儿了
```

Replace the paragraph after the two `hugo server` examples with:

```markdown
Open the URL printed by Hugo, normally `http://localhost:1313/`. Hugo watches
content and templates for changes. This repository has Giscus and Kudos
configured, so an ordinary preview may contact `giscus.app` and the configured
Worker. Local reading, navigation, feeds, and authoring remain usable if either
service is unavailable. Homepage live ranking succeeds only when the Worker
allows the exact `http://localhost:1313` origin; otherwise it shows its safe,
localized unavailable state. Use an uncommitted configuration override with
both integrations disabled when an external-request-free preview is required.
```

Replace the interaction-ID authoring paragraph with:

```markdown
Every published post or project needs a 1–80 character lowercase ASCII
`interactionId` made from letters, numbers, and internal hyphens. It is unique
to one article across both `content/blog/` and `content/projects/`, identical
across that article's language files, and immutable after publication. That
shared value joins both the Giscus discussion and the Kudos count across
translations. Validate it after every content change:
```

Insert this exact section before the existing deployment section:

````markdown
## Content model

The localized site name is **Where Was I** in English and **说哪儿了** in
Chinese. Blog posts live in `content/blog/<slug>/`; polished projects live in
`content/projects/<slug>/`. A project with `projectStatus = "past"` appears in
the homepage Past projects subsection for each language file that exists.

Create a project translation without overwriting an existing file:

```bash
python3 scripts/new_translation.py <slug> en zh --section projects
```

## Popular posts

The homepage ranks only visible blog posts available in the active language.
When at least two candidates exist, it sends one count-only
`GET /<encoded-entity>` request per candidate to the configured Kudos Worker,
sorts after every response succeeds, and shows at most five titles. It never
requests voter state and never displays vote counts. Cloudflare still receives
ordinary request metadata, including the visitor's public IP. A timeout or any
invalid response affects only the Popular posts region.

Production CORS allows `https://allanware.github.io`. To preview the live
ranking at `http://localhost:1313`, add that exact origin to the Worker's
`ALLOWED_ORIGINS`; otherwise the localized unavailable state is expected.
````

Replace the source-archive paragraph with:

```markdown
The three root Markdown files and `writings-images/` remain untouched,
untracked migration inputs. Hugo publishes ordinary posts from `content/blog/`
and publishes the Beyond project bundle from
`content/projects/beyond-the-cloud/`.
```

- [ ] **Step 4: Run the complete automated verification matrix**

Run, in order:

```bash
python3 -m unittest discover -s tests -v
node --test tests/*.test.mjs
python3 scripts/validate_interaction_ids.py
node --check assets/js/post-search.mjs
node --check assets/js/kudos.mjs
node --check assets/js/popular-posts.mjs
actionlint
git diff --check
git diff --cached --check
```

Expected: every command exits 0. The exact test totals must be taken from this fresh run and recorded in the final handoff rather than copied from the pre-feature baseline.

- [ ] **Step 5: Run warning-fatal root and project builds with the checker**

Run:

```bash
root_public=$(mktemp -d)/public
hugo --source . --destination "$root_public" --baseURL https://example.test/ \
  --cleanDestinationDir --panicOnWarning --noBuildLock --gc --minify \
  --environment production --printI18nWarnings --printPathWarnings
python3 scripts/check_site.py "$root_public" --base-url https://example.test/

project_public=$(mktemp -d)/public
hugo --source . --destination "$project_public" \
  --baseURL https://example.test/example-blog/ --cleanDestinationDir \
  --panicOnWarning --noBuildLock --gc --minify --environment production \
  --printI18nWarnings --printPathWarnings
python3 scripts/check_site.py "$project_public" \
  --base-url https://example.test/example-blog/
```

Expected: both Hugo builds exit 0 with no warnings and both checkers print `base-path verification passed`.

- [ ] **Step 6: Run a local mobile/browser acceptance pass**

Resolve the temporary targets before writing anything:

```bash
test ! -e .browser-acceptance
test ! -e /private/tmp/blog-home-browser-public
mkdir .browser-acceptance
mkdir /private/tmp/blog-home-browser-public
```

Create `.browser-acceptance/local.toml` with `apply_patch`:

```toml
[params.kudos]
  enabled = true
  endpoint = "http://localhost:4174"
```

Create `.browser-acceptance/popular-mock.mjs` with `apply_patch`:

```javascript
import http from "node:http";

const counts = new Map([
  ["post:lekythos-a-shape", 2],
  ["post:the-miracle-of-istanbul", 5],
  ["post:beyond-the-cloud", 7],
]);
const voterState = new Map();
let offline = false;
let requests = [];

function send(response, status, body, origin = "*") {
  response.writeHead(status, {
    "access-control-allow-headers": "content-type",
    "access-control-allow-methods": "GET, POST, DELETE, OPTIONS",
    "access-control-allow-origin": origin,
    "cache-control": "no-store",
    "content-type": "application/json; charset=utf-8",
    vary: "Origin",
  });
  response.end(JSON.stringify(body));
}

const server = http.createServer((request, response) => {
  const url = new URL(request.url, "http://localhost:4174");
  const origin = request.headers.origin ?? "*";
  if (request.method === "POST" && url.pathname === "/__mode/success") {
    offline = false;
    requests = [];
    send(response, 200, { mode: "success" }, origin);
    return;
  }
  if (request.method === "POST" && url.pathname === "/__mode/offline") {
    offline = true;
    requests = [];
    send(response, 200, { mode: "offline" }, origin);
    return;
  }
  if (request.method === "GET" && url.pathname === "/__requests") {
    send(response, 200, requests, origin);
    return;
  }
  if (request.method === "OPTIONS") {
    send(response, 204, {}, origin);
    return;
  }

  const parts = url.pathname.split("/").filter(Boolean);
  let entity;
  try {
    entity = decodeURIComponent(parts[0] ?? "");
  } catch {
    send(response, 400, { error: "bad entity" }, origin);
    return;
  }
  requests.push({ method: request.method, path: url.pathname, origin });
  if (offline) {
    send(response, 503, { error: "offline" }, origin);
    return;
  }
  if (!counts.has(entity)) {
    send(response, 404, { error: "unknown entity" }, origin);
    return;
  }
  if (parts.length === 1 && request.method === "GET") {
    send(response, 200, { entity, count: counts.get(entity) }, origin);
    return;
  }
  if (parts.length === 2 && parts[1] === "kudos") {
    if (request.method === "GET") {
      send(response, 200, { entity, hasKudos: voterState.get(entity) ?? false }, origin);
      return;
    }
    if (request.method === "POST") {
      if (!(voterState.get(entity) ?? false)) counts.set(entity, counts.get(entity) + 1);
      voterState.set(entity, true);
      send(
        response,
        200,
        { entity, count: counts.get(entity), hasKudos: true },
        origin,
      );
      return;
    }
    if (request.method === "DELETE") {
      if (voterState.get(entity) ?? false) counts.set(entity, counts.get(entity) - 1);
      voterState.set(entity, false);
      send(
        response,
        200,
        { entity, count: counts.get(entity), hasKudos: false },
        origin,
      );
      return;
    }
  }
  send(response, 404, { error: "unsupported route" }, origin);
});

server.listen(4174, "127.0.0.1", () => {
  process.stdout.write("popular mock listening on http://localhost:4174\n");
});
```

Build both URL shapes under one served directory:

```bash
hugo --source . --destination /private/tmp/blog-home-browser-public \
  --baseURL http://localhost:1313/ --cleanDestinationDir --noBuildLock \
  --environment production \
  --config hugo.toml,.browser-acceptance/local.toml
hugo --source . \
  --destination /private/tmp/blog-home-browser-public/example-blog \
  --baseURL http://localhost:1313/example-blog/ --cleanDestinationDir \
  --noBuildLock --environment production \
  --config hugo.toml,.browser-acceptance/local.toml
```

Start these commands in separate retained PTY sessions:

```bash
node .browser-acceptance/popular-mock.mjs
python3 -m http.server 1313 --bind 127.0.0.1 \
  --directory /private/tmp/blog-home-browser-public
```

Use the Playwright skill against the exact
origin `http://localhost:1313`, aborting `https://giscus.app/**` so the smoke
test never contacts Giscus. Do not route or intercept the localhost Worker.

Set success mode with:

```bash
curl -fsS -X POST http://localhost:4174/__mode/success
```

For each English homepage URL (`/`, then `/example-blog/`), call that reset
immediately before navigation, navigate directly to the homepage, wait for
`[data-popular-state="ready"]`, assert the ordered titles are “The Miracle of
Istanbul” then “Shapes and Functions of the Lekythos”, and inspect
`/__requests` before visiting any article or tag route. For each corresponding
Chinese homepage, reset success mode, navigate directly, assert there is no
`[data-popular-posts]`, and inspect the still-empty request log before leaving.

Only after those isolated request-log checks, use a real 390-pixel-wide browser
to verify:

- the tab uses the supplied hands artwork;
- header title and document title are `Where Was I`, with `说哪儿了` after language switching;
- intro, Projects/Past projects, Latest posts, and Popular posts appear in order;
- Beyond appears only under English Past projects and keeps its PDF/Giscus/Kudos;
- Latest has two English title links and no Chinese links;
- a mocked successful Worker response orders the two English popular links without visible counts;
- a mocked Worker outage reveals only the localized unavailable state;
- tag `visualization` shows Projects before any Posts group;
- under both Playwright `light` and `dark` color-scheme emulation, the intro,
  section headings, links, Popular status, and article Kudos state remain
  readable at both `/` and `/example-blog/`;
- `document.documentElement.scrollWidth <= document.documentElement.clientWidth`
  in both schemes at both base paths; and
- no page error, unhandled rejection, broken favicon request, or root escape
  occurs at root or `/example-blog/`.

After each isolated English-homepage load, inspect:

```bash
curl -fsS http://localhost:4174/__requests
```

The log must contain exactly two homepage `GET` requests, for
`/post%3Alekythos-a-shape` and `/post%3Athe-miracle-of-istanbul`; neither path
may end in `/kudos`, contain `%253A`, or have an origin other than
`http://localhost:1313`. After resetting success mode, `/zh/` must generate an
empty request log. Repeat success checks at `/example-blog/`.

Immediately before each English outage case, set outage mode, navigate directly
to that homepage, wait for `[data-popular-state="error"]`, and assert the
candidate list stays hidden while the localized unavailable message appears.
Inspect the request log before visiting any other route; it may contain one or
two GETs depending on when abort reaches the sibling request, but every entry
must be one of the two expected count-only paths, use the exact localhost
origin, and omit `/kudos`:

```bash
curl -fsS -X POST http://localhost:4174/__mode/offline
```

Stop both retained sessions, delete the two named `.browser-acceptance` files
with `apply_patch`, remove the now-empty `.browser-acceptance` directory, and
remove only the validated `/private/tmp/blog-home-browser-public` directory
after the pass. This procedure
changes neither Cloudflare nor Giscus state; `localhost` exactly matches the
origin documented for optional live local CORS.

After the two `apply_patch` deletions, run:

```bash
rmdir .browser-acceptance
test "$(realpath /private/tmp/blog-home-browser-public)" = \
  "/private/tmp/blog-home-browser-public"
rm -rf /private/tmp/blog-home-browser-public
```

- [ ] **Step 7: Commit documentation after acceptance**

If browser acceptance exposes a product defect, return to the owning task, add
a failing automated regression, fix it, and rerun that task before continuing.
Do not hide a production correction inside the documentation commit.

```bash
git add README.md tests/test_repository.py
git commit -m "docs: document projects and live popularity"
```

- [ ] **Step 8: Repeat the full matrix after the final feature commit**

Run from the feature worktree:

```bash
python3 -m unittest discover -s tests -v
node --test tests/*.test.mjs
python3 scripts/validate_interaction_ids.py
node --check assets/js/post-search.mjs
node --check assets/js/kudos.mjs
node --check assets/js/popular-posts.mjs
actionlint
git diff --check
git diff --cached --check

final_root_public=$(mktemp -d)/public
hugo --source . --destination "$final_root_public" \
  --baseURL https://example.test/ --cleanDestinationDir --panicOnWarning \
  --noBuildLock --gc --minify --environment production \
  --printI18nWarnings --printPathWarnings
python3 scripts/check_site.py "$final_root_public" \
  --base-url https://example.test/

final_project_public=$(mktemp -d)/public
hugo --source . --destination "$final_project_public" \
  --baseURL https://example.test/example-blog/ --cleanDestinationDir \
  --panicOnWarning --noBuildLock --gc --minify --environment production \
  --printI18nWarnings --printPathWarnings
python3 scripts/check_site.py "$final_project_public" \
  --base-url https://example.test/example-blog/
```

Expected: all commands exit 0 after the final commit; neither checker reports
a diagnostic.

- [ ] **Step 9: Final feature-worktree scope audit**

Run:

```bash
git status --short
git log --oneline main..HEAD
git ls-files beyond-the-cloud.md lekythos-a-shape.md the-miracle-of-istanbul.md writings-images
git diff main...HEAD -- themes/hugo-bearneo
```

Expected:

- the implementation worktree has no untracked or modified files;
- `drawing_hands.png` no longer exists at the root and its tracked copy is under `assets/images/`;
- the vendored theme diff is empty;
- the six planned slice commits are present (plus only any separately justified
  regression commit created through Step 7); and
- no production source or required asset remains unstaged.

Separately run `git -C /Users/allan/GitHub/blog status --short` and confirm the
original workspace still contains the three root Markdown files and
`writings-images/` as untouched untracked migration inputs.

- [ ] **Step 10: Fast-forward the verified feature into local `main`**

First prove the original workspace has no tracked or staged edits; its expected
untracked migration inputs do not block a fast-forward:

```bash
test "$(git -C /Users/allan/GitHub/blog symbolic-ref --short HEAD)" = "main"
git -C /Users/allan/GitHub/blog diff --quiet
git -C /Users/allan/GitHub/blog diff --cached --quiet
git -C /Users/allan/GitHub/blog merge --ff-only feat/homepage-projects-popular
test "$(git -C /Users/allan/GitHub/blog rev-parse HEAD)" = "$(git rev-parse HEAD)"
```

If `main` moved after the worktree was created, stop rather than force or create
an implicit merge. Reconcile the new commits, rerun Step 8, and only then retry
the fast-forward.

From `/Users/allan/GitHub/blog`, rerun the release gate on the exact integrated
tree:

```bash
cd /Users/allan/GitHub/blog
python3 -m unittest discover -s tests -v
node --test tests/*.test.mjs
python3 scripts/validate_interaction_ids.py
actionlint

integrated_root_public=$(mktemp -d)/public
hugo --source . --destination "$integrated_root_public" \
  --baseURL https://example.test/ --cleanDestinationDir --panicOnWarning \
  --noBuildLock --gc --minify --environment production \
  --printI18nWarnings --printPathWarnings
python3 scripts/check_site.py "$integrated_root_public" \
  --base-url https://example.test/

integrated_project_public=$(mktemp -d)/public
hugo --source . --destination "$integrated_project_public" \
  --baseURL https://example.test/example-blog/ --cleanDestinationDir \
  --panicOnWarning --noBuildLock --gc --minify --environment production \
  --printI18nWarnings --printPathWarnings
python3 scripts/check_site.py "$integrated_project_public" \
  --base-url https://example.test/example-blog/
```

Expected: the feature and local `main` point to the same commit and every
integrated-tree release check exits 0. Use the finishing-a-development-branch
skill to remove the temporary worktree/branch only after this proof.

- [ ] **Step 11: Publish only with explicit authorization**

After the user authorizes publication, push the now-integrated branch:

```bash
git -C /Users/allan/GitHub/blog push origin main
```

Watch the resulting GitHub Pages Actions run to completion, then check live
`/`, `/zh/`, `/blog/`, `/tags/visualization/`, and `/p/beyond-the-cloud/`.
Verify the live homepage Worker requests are count-only and the live article
still loads both Giscus and Kudos.
