# Blog Collection Labels and Search Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Present blog collections as `Blog`/`博客` on archives and tag pages, use neutral localized search prompts, and make filtered rows and year headings actually disappear.

**Architecture:** Keep the existing Hugo templates, translation keys, and title-matching JavaScript. Change only two localized values per language and restore the native `hidden` contract with one site-scoped CSS rule that overrides the list layout declarations. Python generated-site tests will lock the visible wording and CSS contract; real-browser checks will prove computed visibility that the Node fake DOM cannot model.

**Tech Stack:** Hugo 0.164 Go templates and i18n TOML, CSS, Python 3.11+ `unittest`, Node.js 22+ tests, and Playwright with installed Chrome for computed browser behavior.

---

## File map and constraints

- Modify `i18n/en.toml`: only the visible values for `searchPosts` and `posts`.
- Modify `i18n/zh.toml`: only the corresponding Chinese values.
- Modify `assets/css/site.css`: add the scoped hidden-row rule after the explicit year-row display rules.
- Modify `tests/test_site.py`: update generated-label expectations and add the CSS regression contract.
- Do not modify `assets/js/post-search.mjs`, Hugo templates, `hugo.toml`, content, README prose, internal translation keys, data attributes, or the vendored theme.
- Preserve `No matching posts`, result counts, empty states, metadata descriptions, homepage latest/popular wording, RSS descriptions, popular-post states, and individual article actions in both languages.

### Task 1: Localize Blog collection labels without changing item wording

**Files:**
- Modify: `tests/test_site.py:3007-3120`
- Modify: `tests/test_site.py:3230-3369`
- Modify: `tests/test_site.py:3615-3721`
- Modify: `i18n/en.toml:17-18,55-56`
- Modify: `i18n/zh.toml:17-18,55-56`

- [ ] **Step 1: Change generated-site expectations first**

In `test_tag_results_group_projects_before_posts`, replace only the tag
post-group heading assertions and indexes:

```python
self.assertIn(">Projects</h3>", english)
self.assertIn(">Blog</h3>", english)
self.assertLess(
    english.index(">Projects</h3>"),
    english.index(">Blog</h3>"),
)

self.assertIn(">项目</h3>", chinese)
self.assertIn(">博客</h3>", chinese)
self.assertLess(
    chinese.index(">项目</h3>"),
    chinese.index(">博客</h3>"),
)
```

Keep the `data-tag-group="posts"` selectors and all article-title assertions
unchanged. In that same test, update the searchable Chinese Blog group prompt:

```python
self.assertIn('placeholder="搜索..."', chinese_posts)
```

In `test_searchable_tag_groups_share_one_module`, change only the post-group
placeholder fields in the two expected tuples:

```python
(
    "posts",
    "{count} post",
    "{count} posts",
    "Search...",
    "No matching posts",
),
```

```python
(
    "posts",
    "{count} 篇文章",
    "{count} 篇文章",
    "搜索...",
    "没有匹配的文章",
),
```

In `test_populated_multilingual_post_and_tag_pages`, strengthen the existing
archive subtests with the neutral prompts while retaining the item strings:

```python
self.assertIn('placeholder="Search..."', english_blog)
self.assertIn("No matching posts", english_blog)
self.assertIn('data-count-one="{count} post"', english_blog)
self.assertIn('data-count-many="{count} posts"', english_blog)
```

```python
self.assertIn('placeholder="搜索..."', chinese_blog)
self.assertIn("没有匹配的文章", chinese_blog)
self.assertIn('data-count-one="{count} 篇文章"', chinese_blog)
self.assertIn('data-count-many="{count} 篇文章"', chinese_blog)
```

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
python3 -B -m unittest \
  tests.test_site.GeneratedSiteTests.test_tag_results_group_projects_before_posts \
  tests.test_site.GeneratedSiteTests.test_searchable_tag_groups_share_one_module \
  tests.test_site.GeneratedSiteTests.test_populated_multilingual_post_and_tag_pages \
  -v
```

Expected: failures show the old `Posts`/`文章` headings and
`Search posts`/`搜索文章` placeholders. Count and no-match assertions continue to
pass.

- [ ] **Step 3: Change only the four localized values**

In `i18n/en.toml`:

```toml
[searchPosts]
other = "Search..."
```

```toml
[posts]
other = "Blog"
```

In `i18n/zh.toml`:

```toml
[searchPosts]
other = "搜索..."
```

```toml
[posts]
other = "博客"
```

Do not rename the keys or change `noSearchResults`, `postCount`, `noPosts`,
`rssDescription`, `latestPosts`, `popularPosts`, or any popular-post state.

- [ ] **Step 4: Run focused wording regressions and verify GREEN**

```bash
python3 -B -m unittest \
  tests.test_site.GeneratedSiteTests.test_tag_results_group_projects_before_posts \
  tests.test_site.GeneratedSiteTests.test_searchable_tag_groups_share_one_module \
  tests.test_site.GeneratedSiteTests.test_populated_multilingual_post_and_tag_pages \
  tests.test_site.GeneratedSiteTests.test_post_search_has_localized_no_match_feedback \
  tests.test_site.GeneratedSiteTests.test_home_sections_are_ordered_title_only_and_language_local \
  tests.test_site.GeneratedSiteTests.test_rss_is_separate_and_localized \
  -v
```

Expected: all tests pass. Generated tag headings and Blog-list prompts use the
new collection wording, while home, no-match, count, and RSS copy stays
post-oriented.

- [ ] **Step 5: Audit and commit Task 1**

```bash
git diff --check -- i18n/en.toml i18n/zh.toml tests/test_site.py
git diff -- i18n/en.toml i18n/zh.toml tests/test_site.py
git add i18n/en.toml i18n/zh.toml tests/test_site.py
git diff --cached --check
git commit -m "refactor: label tagged post collections as Blog"
```

Expected: the commit contains only four translation-value changes and their
generated-site expectations.

### Task 2: Restore native hidden behavior for filtered list rows

**Files:**
- Modify: `tests/test_site.py` immediately after `test_year_heading_optically_aligns_with_date_text`
- Modify: `assets/css/site.css:145-153`

- [ ] **Step 1: Add the failing CSS contract test**

Add this focused method to `GeneratedSiteTests`:

```python
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
```

- [ ] **Step 2: Run the new test and verify RED**

```bash
python3 -B -m unittest \
  tests.test_site.GeneratedSiteTests.test_filtered_post_rows_override_list_display_rules \
  -v
```

Expected: FAIL because no `ul.blog-posts li[hidden]` rule exists.

- [ ] **Step 3: Add the minimal site-scoped CSS override**

Immediately after the existing `ul.blog-posts li.post-year h3` rule in
`assets/css/site.css`, add:

```css
ul.blog-posts li[hidden] {
  display: none !important;
}
```

Do not change `post-search.mjs`: it already sets and clears the `hidden`
property correctly.

- [ ] **Step 4: Run focused CSS and search regressions and verify GREEN**

```bash
python3 -B -m unittest \
  tests.test_site.GeneratedSiteTests.test_filtered_post_rows_override_list_display_rules \
  tests.test_site.GeneratedSiteTests.test_year_group_headings_align_with_grouped_date_columns \
  tests.test_site.GeneratedSiteTests.test_year_heading_optically_aligns_with_date_text \
  -v
node --test tests/post-search.test.mjs
```

Expected: Python reports three passing tests; Node reports six passing search
tests. Year headings retain block layout when visible, and JavaScript remains
unchanged.

- [ ] **Step 5: Audit and commit Task 2**

```bash
git diff --check -- assets/css/site.css tests/test_site.py
git diff -- assets/css/site.css tests/test_site.py
git add assets/css/site.css tests/test_site.py
git diff --cached --check
git commit -m "fix: hide filtered Blog rows"
```

Expected: the commit contains one CSS rule and one focused regression method.

### Task 3: Verify computed search behavior and the complete site

**Files:**
- Verify only; no source changes expected.

- [ ] **Step 1: Start an isolated actual-content Hugo server**

Run in a retained terminal from the repository root:

```bash
hugo server --bind 127.0.0.1 --port 13135 --disableFastRender \
  --disableLiveReload --renderToMemory --noBuildLock \
  --baseURL http://127.0.0.1:13135/
```

Expected: Hugo reports the server at `http://127.0.0.1:13135/`. Do not stop or
reuse an unrelated server on another port.

- [ ] **Step 2: Verify Istanbul, no-results, and clear-search behavior in Chrome**

Locate the already installed Playwright package and Chrome, then run:

```bash
PW_PACKAGE="$(find "$(npm config get cache)/_npx" \
  -path '*/node_modules/playwright/package.json' -print -quit)"
test -n "$PW_PACKAGE"
export BLOG_SEARCH_PLAYWRIGHT_ROOT="$(dirname "$PW_PACKAGE")"
export BLOG_SEARCH_CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
test -x "$BLOG_SEARCH_CHROME"
node - <<'NODE'
const assert = require('node:assert/strict');
const { chromium } = require(process.env.BLOG_SEARCH_PLAYWRIGHT_ROOT);

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.BLOG_SEARCH_CHROME,
    headless: true,
  });
  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:13135/blog/', { waitUntil: 'load' });
  const input = page.locator('[data-post-search]');

  async function state() {
    return page.evaluate(() => {
      const isRendered = (element) =>
        getComputedStyle(element).display !== 'none' &&
        element.getClientRects().length > 0;
      const empty = document.querySelector('[data-search-empty]');
      return {
        items: [...document.querySelectorAll('[data-post-item]')]
          .filter(isRendered)
          .map((item) => item.dataset.postTitle),
        years: [...document.querySelectorAll('.post-year[data-post-year]')]
          .filter(isRendered)
          .map((year) => year.dataset.postYear),
        emptyVisible: isRendered(empty),
        emptyText: empty.textContent.trim(),
        status: document.querySelector('[data-search-status]').textContent,
      };
    });
  }

  await input.fill('istanbul');
  assert.deepEqual(await state(), {
    items: ['The Miracle of Istanbul'],
    years: ['2021'],
    emptyVisible: false,
    emptyText: 'No matching posts',
    status: '1 post',
  });

  await input.fill('not-a-real-title-xyz');
  assert.deepEqual(await state(), {
    items: [],
    years: [],
    emptyVisible: true,
    emptyText: 'No matching posts',
    status: 'No matching posts',
  });

  await input.fill('');
  const cleared = await state();
  assert.deepEqual(cleared.items, [
    'Shapes and Functions of the Lekythos',
    'The Miracle of Istanbul',
  ]);
  assert.deepEqual(cleared.years, ['2022', '2021']);
  assert.equal(cleared.emptyVisible, false);
  assert.equal(cleared.status, '2 posts');

  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
NODE
```

Expected: the script exits zero. Before the CSS fix, its first assertion fails
because both rows and both years still have layout boxes.

- [ ] **Step 3: Stop the actual-content server**

Send `Ctrl-C` to the exact server session from Step 1.

Expected: the port-13135 Hugo process exits cleanly.

- [ ] **Step 4: Start an isolated multilingual fixture server**

```bash
hugo server --bind 127.0.0.1 --port 13136 --disableFastRender \
  --disableLiveReload --renderToMemory --noBuildLock \
  --baseURL http://127.0.0.1:13136/ \
  --config hugo.toml,tests/fixtures/interactions.toml \
  --contentDir tests/fixtures/content
```

Expected: the fixture server reports `http://127.0.0.1:13136/`.

- [ ] **Step 5: Verify localized labels, preserved home copy, and tag filtering**

Reuse the two exported browser paths from Step 2:

```bash
node - <<'NODE'
const assert = require('node:assert/strict');
const { chromium } = require(process.env.BLOG_SEARCH_PLAYWRIGHT_ROOT);

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.BLOG_SEARCH_CHROME,
    headless: true,
  });
  const page = await browser.newPage();

  await page.goto('http://127.0.0.1:13136/blog/', { waitUntil: 'load' });
  assert.equal(await page.locator('main h2').textContent(), 'Blog');
  assert.equal(await page.locator('[data-post-search]').getAttribute('placeholder'), 'Search...');

  await page.goto('http://127.0.0.1:13136/zh/blog/', { waitUntil: 'load' });
  assert.equal(await page.locator('main h2').textContent(), '博客');
  assert.equal(await page.locator('[data-post-search]').getAttribute('placeholder'), '搜索...');

  await page.goto('http://127.0.0.1:13136/tags/fixture/', { waitUntil: 'load' });
  assert.equal(
    await page.locator('[data-tag-group="posts"] > h3').textContent(),
    'Blog',
  );
  assert.equal(
    await page.locator('[data-tag-group="projects"] > h3').textContent(),
    'Projects',
  );

  await page.goto('http://127.0.0.1:13136/zh/tags/%E6%B5%8B%E8%AF%95/', { waitUntil: 'load' });
  const group = page.locator('[data-tag-group="posts"]');
  assert.equal(await group.locator(':scope > h3').textContent(), '博客');
  const input = group.locator('[data-post-search]');
  assert.equal(await input.getAttribute('placeholder'), '搜索...');
  await input.fill('共享');
  assert.deepEqual(
    await group.locator('[data-post-item]:visible').evaluateAll((items) =>
      items.map((item) => item.dataset.postTitle),
    ),
    ['共享文章'],
  );
  assert.equal(
    await page.locator('[data-tag-group="projects"] [data-post-item]:visible').count(),
    1,
  );

  await input.fill('完全不相关');
  assert.equal(await group.locator('[data-post-item]:visible').count(), 0);
  assert.equal(await group.locator('.post-year:visible').count(), 0);
  assert.equal(await group.locator('[data-search-empty]').textContent(), '没有匹配的文章');

  await input.fill('');
  assert.equal(await group.locator('[data-post-item]:visible').count(), 2);

  await page.goto('http://127.0.0.1:13136/', { waitUntil: 'load' });
  assert.equal(await page.locator('[data-home-section="latest"] h2').textContent(), 'Latest posts');
  assert.equal(await page.locator('[data-home-section="popular"] h2').textContent(), 'Popular posts');

  await page.goto('http://127.0.0.1:13136/zh/', { waitUntil: 'load' });
  assert.equal(await page.locator('[data-home-section="latest"] h2').textContent(), '最新文章');
  assert.equal(await page.locator('[data-home-section="popular"] h2').textContent(), '热门文章');

  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
NODE
```

Expected: every assertion passes. The Blog group filters independently, while
the project group and home-page post wording remain unchanged.

- [ ] **Step 6: Stop the fixture server**

Send `Ctrl-C` to the exact server session from Step 4.

Expected: the port-13136 Hugo process exits cleanly.

- [ ] **Step 7: Run the complete automated and build verification**

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
python3 -B scripts/validate_interaction_ids.py content
node --check assets/js/post-search.mjs
node --check assets/js/kudos.mjs
node --check assets/js/popular-posts.mjs
actionlint .github/workflows/hugo.yml
```

Then build both deployment URL shapes in exact temporary directories:

```bash
BLOG_SEARCH_ROOT_BUILD="$(mktemp -d)"
BLOG_SEARCH_SUBPATH_BUILD="$(mktemp -d)"
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.test/ \
  --destination "$BLOG_SEARCH_ROOT_BUILD"
python3 scripts/check_site.py "$BLOG_SEARCH_ROOT_BUILD" \
  --base-url https://example.test/
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.test/example-blog/ \
  --destination "$BLOG_SEARCH_SUBPATH_BUILD"
python3 scripts/check_site.py "$BLOG_SEARCH_SUBPATH_BUILD" \
  --base-url https://example.test/example-blog/
rm -rf "$BLOG_SEARCH_ROOT_BUILD" "$BLOG_SEARCH_SUBPATH_BUILD"
```

Expected: every test/lint/syntax command exits zero; both Hugo builds complete
without warnings; both checker runs print `base-path verification passed`; and
only the two exact temporary build directories are removed.

- [ ] **Step 8: Audit final scope and request review**

```bash
git status --short --branch
git diff --check
git log -5 --oneline
git diff HEAD~2..HEAD -- \
  assets/css/site.css i18n/en.toml i18n/zh.toml tests/test_site.py
```

Expected: the two implementation commits follow the design, no unrelated files
changed, the JavaScript and vendored theme remain untouched, and the worktree is
clean. Invoke the requesting-code-review workflow before branch integration.
