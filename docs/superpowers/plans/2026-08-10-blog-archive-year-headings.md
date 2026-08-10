# Blog Archive Year Headings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align semantic year headings with grouped dates on blog and individual-tag lists, rename both localized blog archive identities, and remove the archives' visible post counts without weakening search behavior.

**Architecture:** Keep the existing valid `li.post-year[data-post-year]` search boundary and render an `h3` inside it. A site-local CSS override supplies the reference spacing and block layout while the vendored 80-pixel date column remains unchanged. Archive-specific count suppression stays at the blog-section caller, and localized archive titles/menu labels remain content and configuration concerns.

**Tech Stack:** Hugo 0.164 Go templates, HTML/CSS, Python 3.11+ `unittest`, Node.js 22+ tests, and Playwright with installed Chrome for computed-layout verification.

---

## File map

- Modify `layouts/_partials/post-list.html`: render each shared year marker as an `h3` while preserving its list item and search metadata.
- Modify `assets/css/site.css`: restore the reference heading block layout, zero horizontal margin, and 16-pixel vertical spacing.
- Modify `layouts/blog/section.html`: suppress the visible count only for localized blog archives.
- Modify `content/blog/_index.en.md`: change the English archive/content metadata title to `Blog`.
- Modify `content/blog/_index.zh.md`: change the Chinese archive/content metadata title to `博客`.
- Modify `hugo.toml`: change only the English and Chinese `/blog` menu labels.
- Modify `README.md`: document `Home`, `Blog`, and `Tags` as the primary destinations.
- Modify `tests/test_site.py`: cover shared year semantics, archive/tag scope, localized titles/navigation, count suppression, and retained search contracts.
- Modify `tests/post-search.test.mjs`: prove filtering and live announcements work when no visible count node exists.
- Modify `tests/test_repository.py`: keep the documented navigation contract synchronized.
- Do not modify `themes/hugo-bearneo/layouts/partials/style.html`, `layouts/term.html`, either `i18n/*.toml` file, `assets/js/post-search.mjs`, or the localized prose descriptions in `hugo.toml`.

## Working-tree constraint

The workspace already contains changes that are outside this plan. Before editing, capture their exact state:

```bash
git status --short
git diff -- content/_index.en.md content/_index.zh.md \
  layouts/_partials/post-list.html tests/test_site.py
```

Expected: the two home index files have unrelated content edits, while the post-list partial and site tests contain in-progress long-month abbreviation work. Preserve every one of those hunks. When a task touches `layouts/_partials/post-list.html` or `tests/test_site.py`, use interactive staging and inspect the cached patch so only that task's new hunks enter its commit.

### Task 1: Semantic, aligned year headings in every shared list

**Files:**
- Modify: `tests/test_site.py` near the grouped-list generated tests
- Modify: `layouts/_partials/post-list.html:36-52`
- Modify: `assets/css/site.css` before the existing small-screen post-search rule

- [ ] **Step 1: Add a failing archive-and-tag heading contract test**

Add this method to `GeneratedSiteTests` in `tests/test_site.py`, outside the existing dirty month-format test:

```python
def test_year_group_headings_align_with_grouped_date_columns(self):
    site_css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
    theme_css = (
        ROOT / "themes/hugo-bearneo/layouts/partials/style.html"
    ).read_text(encoding="utf-8")
    self.assertRegex(
        site_css,
        r"ul\.blog-posts li\.post-year\s*\{[^}]*"
        r"display:\s*block;[^}]*\}",
    )
    self.assertRegex(
        site_css,
        r"ul\.blog-posts li\.post-year h3\s*\{[^}]*"
        r"margin:\s*16px\s+0;[^}]*\}",
    )
    self.assertRegex(
        theme_css,
        r"ul\.blog-posts li span\.grouped\s*\{[^}]*"
        r"flex:\s*0\s+0\s+80px;[^}]*\}",
    )

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
        english_blog = read_html(public, "blog/index.html")
        chinese_blog = read_html(public, "zh/blog/index.html")
        english_tag = read_html(public, "tags/fixture/index.html")
        chinese_tag = read_html(public, "zh/tags/测试/index.html")
        year_heading = (
            '<li class="post-year" data-post-year="2026">'
            "<h3>2026</h3></li>"
        )

        for page, html in (
            ("English archive", english_blog),
            ("Chinese archive", chinese_blog),
        ):
            with self.subTest(page=page):
                self.assertIn(year_heading, html)
                self.assertNotIn("<strong>2026</strong>", html)

        for language, html in (
            ("English", english_tag),
            ("Chinese", chinese_tag),
        ):
            for group_name in ("projects", "posts"):
                with self.subTest(language=language, group=group_name):
                    match = re.search(
                        rf'<section data-tag-group="{group_name}">'
                        r"(.*?)</section>",
                        html,
                        re.DOTALL,
                    )
                    self.assertIsNotNone(match)
                    self.assertIn(year_heading, match.group(1))
                    self.assertNotIn("<strong>2026</strong>", match.group(1))
```

- [ ] **Step 2: Run the heading contract test and verify RED**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_year_group_headings_align_with_grouped_date_columns \
  -v
```

Expected: FAIL because site-local year CSS is absent and generated year markers still contain `strong`.

- [ ] **Step 3: Render the year as a heading without disturbing date formatting**

In `layouts/_partials/post-list.html`, change only the year-marker line to:

```go-html-template
{{ if $page.Site.Params.groupByYear }}<li class="post-year" data-post-year="{{ .Key }}"><h3>{{ .Key }}</h3></li>{{ end }}
```

Keep the existing `$rowDateFormat` calculation, long-month abbreviation comment, and visible `<time>` rendering byte-for-byte unchanged.

- [ ] **Step 4: Add the site-local block and spacing override**

Add this to `assets/css/site.css` before the post-search media query:

```css
ul.blog-posts li.post-year {
  display: block;
}

ul.blog-posts li.post-year h3 {
  margin: 16px 0;
}
```

The selector overrides the vendored `ul.blog-posts li { display: flex; }` rule. The two-value margin supplies 16 pixels vertically and zero pixels horizontally; do not duplicate or alter the inherited `80px` grouped-date flex basis.

- [ ] **Step 5: Run focused heading and date regressions and verify GREEN**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_year_group_headings_align_with_grouped_date_columns \
  tests.test_site.GeneratedSiteTests.test_grouped_lists_use_localized_dates_without_repeating_year \
  tests.test_site.GeneratedSiteTests.test_grouped_list_abbreviates_long_month_names \
  -v
```

Expected: three tests PASS. This confirms the new heading structure reaches both archive and tag callers without regressing the existing month/date work.

- [ ] **Step 6: Commit only Task 1 hunks**

Stage the clean CSS file normally and interactively select only the new heading-test and `strong`-to-`h3` hunks from the two dirty files:

```bash
git add assets/css/site.css
git add -p layouts/_partials/post-list.html tests/test_site.py
git diff --cached --check
git diff --cached -- assets/css/site.css layouts/_partials/post-list.html tests/test_site.py
git commit -m "style: align grouped year headings with dates"
```

Expected cached scope: the CSS rules, the year element replacement, and the new heading contract test. The pre-existing month abbreviation hunks remain unstaged.

### Task 2: Localized Blog identity and archive-only count suppression

**Files:**
- Modify: `tests/test_site.py`
- Modify: `tests/post-search.test.mjs`
- Modify: `tests/test_repository.py:164-175`
- Modify: `layouts/blog/section.html:2-6`
- Modify: `content/blog/_index.en.md:1-3`
- Modify: `content/blog/_index.zh.md:1-3`
- Modify: `hugo.toml:79-83,111-115`
- Modify: `README.md:8-10`

- [ ] **Step 1: Change generated-site expectations before implementation**

Make these exact assertion changes in the named `GeneratedSiteTests` methods.

In `test_root_and_project_subpath_production_matrix_is_complete`:

```python
english_blog = read_html(public, "blog/index.html")
chinese_blog = read_html(public, "zh/blog/index.html")
expected_navigation = [
    (f"{base_path}", "Home"),
    (f"{base_path}blog/", "Blog"),
    (f"{base_path}tags/", "Tags"),
]
expected_chinese_navigation = [
    (f"{base_path}zh/", "首页"),
    (f"{base_path}zh/blog/", "博客"),
    (f"{base_path}zh/tags/", "标签"),
]
for html, page_title, site_title, navigation in (
    (english_blog, "Blog", "Where Was I", expected_navigation),
    (chinese_blog, "博客", "说哪儿了", expected_chinese_navigation),
):
    with self.subTest(build=name, archive=page_title):
        self.assertEqual(navigation, primary_navigation(html))
        self.assertIn(f"<title>{page_title} | {site_title}</title>", html)
        self.assertIn(f"<h2>{page_title}</h2>", html)
        for attribute, selector in (
            ("name", "title"),
            ("property", "og:title"),
            ("name", "twitter:title"),
            ("itemprop", "name"),
        ):
            self.assertRegex(
                html,
                rf'<meta {attribute}="?{selector}"? '
                rf'content="?{re.escape(page_title)}"?',
            )
        self.assertNotIn("data-post-count", html)
```

In `test_seo_uses_only_real_translations`, keep the adjacent `data-count-one` and `data-count-many` checks but replace the two visible-count checks with:

```python
self.assertNotIn("data-post-count", english_posts)
self.assertIn('data-count-one="{count} post"', english_posts)
self.assertIn('data-count-many="{count} posts"', english_posts)
self.assertNotIn("data-post-count", chinese_posts)
self.assertIn('data-count-one="{count} 篇文章"', chinese_posts)
self.assertIn('data-count-many="{count} 篇文章"', chinese_posts)
```

In `test_beyond_is_a_project_with_a_stable_public_contract`:

```python
self.assertNotIn("Beyond the Cloud", archive)
self.assertNotIn("data-post-count", archive)
```

In `test_chrome_is_localized_and_uses_browser_color_preference`, update the two header-navigation expectations:

```python
self.assertEqual(
    [("/", "Home"), ("/blog/", "Blog"), ("/tags/", "Tags")],
    primary_navigation(english),
)
self.assertEqual(
    [("/zh/", "首页"), ("/zh/blog/", "博客"), ("/zh/tags/", "标签")],
    primary_navigation(chinese),
)
```

In `test_tag_results_group_projects_before_posts`, preserve the existing `>Posts</h3>` and `>文章</h3>` assertions and replace the populated archive count assertion with:

```python
english_blog = read_html(public, "blog/index.html")
self.assertNotIn("data-post-count", english_blog)
self.assertEqual(1, english_blog.count("data-post-search"))
self.assertEqual(1, english_blog.count("js/post-search."))
```

In `test_populated_multilingual_post_and_tag_pages`, rename the two count subtests and use:

```python
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
    self.assertNotIn("Hidden post", english_blog)

with self.subTest("Chinese list omits its visible count"):
    self.assertEqual(1, chinese_blog.count("data-post-item"))
    self.assertNotIn("data-post-count", chinese_blog)
    self.assertIn('data-count-one="{count} 篇文章"', chinese_blog)
    self.assertIn('data-count-many="{count} 篇文章"', chinese_blog)
```

In `test_grouped_lists_use_localized_dates_without_repeating_year`, strengthen both language loops' existing year-marker assertions to:

```python
self.assertIn(
    '<li class="post-year" data-post-year="2026">'
    "<h3>2026</h3></li>",
    html,
)
```

Within the same root/subpath loop, add the retained search metadata and hidden-count contract for the populated fixture archives. The fixture deliberately has no section index files, so archive identity assertions stay in the production matrix above.

```python
for html, language, count_one, count_many in (
    (
        english_blog,
        "English",
        "{count} post",
        "{count} posts",
    ),
    (
        chinese_blog,
        "Chinese",
        "{count} 篇文章",
        "{count} 篇文章",
    ),
):
    with self.subTest(build=name, archive=language):
        self.assertNotIn("data-post-count", html)
        self.assertIn("data-post-search", html)
        self.assertIn("js/post-search.", html)
        self.assertIn(f'data-count-one="{count_one}"', html)
        self.assertIn(f'data-count-many="{count_many}"', html)
```

- [ ] **Step 2: Add the documentation-contract failure**

In `tests/test_repository.py`, change the navigation assertion to:

```python
self.assertIn("Home, Blog, and Tags", readme)
```

- [ ] **Step 3: Characterize search behavior without a visible count node**

Append this regression to `tests/post-search.test.mjs`; no production JavaScript change should be necessary because `mountPostSearch` already treats the count node as optional:

```javascript
test("filters and announces results without a visible count", () => {
  const { input, items, root, status, years } = createPostList();
  const querySelector = root.querySelector.bind(root);
  root.querySelector = (selector) =>
    selector === "[data-post-count]" ? null : querySelector(selector);
  mountPostSearch(root);

  input.value = "newer";
  input.dispatch("input");

  assert.deepEqual(items.map((item) => item.hidden), [false, true]);
  assert.deepEqual(years.map((year) => year.hidden), [false, true]);
  assert.equal(status.textContent, "1 post");
});
```

- [ ] **Step 4: Run the revised contracts and verify RED where expected**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_root_and_project_subpath_production_matrix_is_complete \
  tests.test_site.GeneratedSiteTests.test_seo_uses_only_real_translations \
  tests.test_site.GeneratedSiteTests.test_beyond_is_a_project_with_a_stable_public_contract \
  tests.test_site.GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference \
  tests.test_site.GeneratedSiteTests.test_tag_results_group_projects_before_posts \
  tests.test_site.GeneratedSiteTests.test_grouped_lists_use_localized_dates_without_repeating_year \
  tests.test_site.GeneratedSiteTests.test_populated_multilingual_post_and_tag_pages \
  tests.test_repository.RepositoryTests.test_authoring_and_operator_contract_is_documented \
  -v
node --test tests/post-search.test.mjs
```

Expected: the Python command FAILS on current `Posts`/`文章` archive labels, visible counts, and README wording. The Node command PASSES, documenting that count removal needs no JavaScript implementation.

- [ ] **Step 5: Rename only the archive titles and menu labels**

Set `content/blog/_index.en.md` to:

```toml
+++
title = "Blog"
+++
```

Set `content/blog/_index.zh.md` to:

```toml
+++
title = "博客"
+++
```

In `hugo.toml`, retain both menu identifiers, page references, and weights while changing only the names:

```toml
[[languages.en.menus.main]]
  identifier = "posts"
  name = "Blog"
  pageRef = "/blog"
  weight = 20

[[languages.zh.menus.main]]
  identifier = "posts"
  name = "博客"
  pageRef = "/blog"
  weight = 20
```

Do not change the `Posts by Wenxuan Zhao` or `赵文轩的文章` descriptions, and do not change the `posts` translations used for individual tag group headings.

- [ ] **Step 6: Suppress the count at the archive caller**

Change the partial call in `layouts/blog/section.html` to:

```go-html-template
{{ partial "post-list.html" (dict "Page" . "Pages" .Pages "ShowCount" false) }}
```

Do not change the global `showPostCount` setting: the shared partial still carries localized `data-count-one` and `data-count-many` strings for its live region, and `layouts/term.html` already passes `ShowCount = false` for tag groups.

- [ ] **Step 7: Update the operator documentation**

Change the README navigation sentence to:

```markdown
The primary navigation intentionally has exactly Home, Blog, and Tags as its
three destinations. English and Chinese have separate post lists and tag
vocabularies. RSS stays available through feed discovery and the footer rather
than becoming a fourth page.
```

Keep the authoring prose that begins `Posts are multilingual leaf bundles` unchanged.

- [ ] **Step 8: Run the focused contracts and verify GREEN**

Re-run the Python and Node commands from Step 4.

Expected: all selected Python tests PASS; the Node file reports zero failures. The individual tag pages still contain `Posts` and `文章` group headings, while their shared year markers contain `h3`.

- [ ] **Step 9: Commit only Task 2 hunks**

```bash
git add README.md content/blog/_index.en.md content/blog/_index.zh.md \
  hugo.toml layouts/blog/section.html tests/post-search.test.mjs \
  tests/test_repository.py
git add -p tests/test_site.py
git diff --cached --check
git diff --cached -- README.md content/blog/_index.en.md \
  content/blog/_index.zh.md hugo.toml layouts/blog/section.html \
  tests/post-search.test.mjs tests/test_repository.py tests/test_site.py
git commit -m "refactor: present post archives as Blog"
```

Expected cached scope: localized archive/menu identities, archive-only count suppression, updated documentation, and their tests. Leave all pre-existing unstaged hunks intact.

### Task 3: Browser geometry and complete regression gate

**Files:**
- Verify only: all Task 1 and Task 2 paths
- Preserve: pre-existing changes in `content/_index.en.md`, `content/_index.zh.md`, `layouts/_partials/post-list.html`, and `tests/test_site.py`

- [ ] **Step 1: Start a populated fixture server on loopback**

Run this in a retained terminal session:

```bash
hugo server --bind 127.0.0.1 --port 1313 --disableFastRender \
  --disableLiveReload --renderToMemory --noBuildLock \
  --baseURL http://127.0.0.1:1313/ \
  --config hugo.toml,tests/fixtures/interactions.toml \
  --contentDir tests/fixtures/content
```

Expected: Hugo reports a Web Server URL at `http://127.0.0.1:1313/` and stays running. Use HTTP rather than `file://`; fingerprinted stylesheets with integrity metadata require normal HTTP loading.

- [ ] **Step 2: Verify computed alignment at desktop and mobile widths**

In a second terminal, locate the already cached Playwright package and run installed Chrome without downloading dependencies:

```bash
PW_PACKAGE="$(find "$(npm config get cache)/_npx" \
  -path '*/node_modules/playwright/package.json' -print -quit)"
test -n "$PW_PACKAGE"
export PLAYWRIGHT_ROOT="$(dirname "$PW_PACKAGE")"
export CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
test -x "$CHROME_BIN"
node - <<'NODE'
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_ROOT);

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_BIN,
    headless: true,
  });
  const page = await browser.newPage();
  const routes = new Map([
    ['/blog/', 1],
    ['/zh/blog/', 1],
    ['/tags/fixture/', 2],
    ['/zh/tags/%E6%B5%8B%E8%AF%95/', 2],
  ]);

  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const [path, expectedLists] of routes) {
      await page.goto(`http://127.0.0.1:1313${path}`, { waitUntil: 'load' });
      const result = await page.evaluate(() => {
        const lists = [
          ...document.querySelectorAll('section.post-list[data-post-list]'),
        ];
        const rows = lists.flatMap((list, listIndex) =>
          [
            ...list.querySelectorAll(
              ':scope > ul.blog-posts > li.post-year[data-post-year]',
            ),
          ].map((marker) => {
            const heading = marker.querySelector(':scope > h3');
            const item = marker.nextElementSibling;
            const date = item?.querySelector(':scope > span.grouped > time');
            if (!heading || !item?.matches('li[data-post-item]') || !date) {
              throw new Error(`Malformed year group ${marker.dataset.postYear}`);
            }
            const headingBox = heading.getBoundingClientRect();
            const dateBox = date.getBoundingClientRect();
            const headingStyle = getComputedStyle(heading);
            return {
              listIndex,
              group:
                list.closest('[data-tag-group]')?.dataset.tagGroup ?? 'archive',
              year: marker.dataset.postYear,
              headingTag: heading.tagName,
              delta: Math.abs(headingBox.left - dateBox.left),
              markerDisplay: getComputedStyle(marker).display,
              margin: `${headingStyle.marginTop} ${headingStyle.marginRight} ${headingStyle.marginBottom} ${headingStyle.marginLeft}`,
              groupedBasis: getComputedStyle(date.parentElement).flexBasis,
            };
          }),
        );
        return { listCount: lists.length, rows };
      });

      assert.equal(result.listCount, expectedLists, `${path}: post-list count`);
      assert.ok(result.rows.length > 0, `${path}: no year groups`);
      for (const row of result.rows) {
        assert.equal(row.headingTag, 'H3', `${path}: year semantics`);
        assert.ok(
          row.delta <= 1,
          `${path}: ${row.group} ${row.year} misaligned by ${row.delta}px`,
        );
        assert.equal(row.markerDisplay, 'block', `${path}: year marker display`);
        assert.equal(
          row.margin,
          '16px 0px 16px 0px',
          `${path}: year spacing`,
        );
        assert.equal(row.groupedBasis, '80px', `${path}: date column`);
      }
      console.log(width, path, result.rows);
    }
  }
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
NODE
```

Expected: the script exits zero for all four localized archive/tag routes at both widths. Every row reports `H3`, a left-coordinate delta no greater than one pixel, block marker layout, `16px 0px 16px 0px` heading margins, and an `80px` grouped flex basis.

- [ ] **Step 3: Stop the retained Hugo server**

Send `Ctrl-C` to the exact terminal session started in Step 1.

Expected: Hugo exits cleanly and no loopback server remains on port 1313.

- [ ] **Step 4: Run the complete automated regression suite**

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
python3 -B scripts/validate_interaction_ids.py content
node --check assets/js/post-search.mjs
node --check assets/js/kudos.mjs
node --check assets/js/popular-posts.mjs
actionlint .github/workflows/hugo.yml
```

Expected: every command exits zero; Python ends with `OK`, Node reports zero failures, the interaction-ID validator succeeds, all JavaScript parses, and the workflow has no lint errors.

- [ ] **Step 5: Build and inspect both deployment URL shapes**

```bash
BLOG_ARCHIVE_ROOT_BUILD="$(mktemp -d)"
BLOG_ARCHIVE_SUBPATH_BUILD="$(mktemp -d)"
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.test/ \
  --destination "$BLOG_ARCHIVE_ROOT_BUILD"
python3 scripts/check_site.py "$BLOG_ARCHIVE_ROOT_BUILD" \
  --base-url https://example.test/
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.test/example-blog/ \
  --destination "$BLOG_ARCHIVE_SUBPATH_BUILD"
python3 scripts/check_site.py "$BLOG_ARCHIVE_SUBPATH_BUILD" \
  --base-url https://example.test/example-blog/
rm -rf "$BLOG_ARCHIVE_ROOT_BUILD" "$BLOG_ARCHIVE_SUBPATH_BUILD"
```

Expected: both Hugo builds complete without warnings, and both checker runs print `base-path verification passed` before the two exact temporary directories are removed.

- [ ] **Step 6: Audit final scope and preserved work**

```bash
git status --short
git diff --check -- README.md assets/css/site.css content/blog/_index.en.md \
  content/blog/_index.zh.md hugo.toml layouts/blog/section.html \
  layouts/_partials/post-list.html tests/post-search.test.mjs \
  tests/test_repository.py tests/test_site.py
git log -3 --oneline
```

Expected: no whitespace errors in task files; the two implementation commits are present; the pre-existing home-content and long-month changes still exist exactly as recorded in the working-tree constraint and have not been restored, overwritten, or accidentally staged.
