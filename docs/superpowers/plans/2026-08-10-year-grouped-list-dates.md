# Year-Grouped List Dates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render localized month/day row dates on every year-grouped Posts and individual-tag list while preserving complete article dates and machine-readable dates.

**Architecture:** Add a language-local `listDateFormat` alongside the existing full `dateFormat`. The shared post-list partial selects the list-specific format with a full-date fallback, so both its archive and term-page callers change consistently without duplicate template logic. Article rendering continues to use the existing full format.

**Tech Stack:** Hugo 0.164 Go templates and language configuration, Python 3.11+ `unittest`, Node.js 22+ tests.

---

## File map

- Modify `tests/test_site.py`: add root/subpath generated assertions for localized yearless list dates and unchanged article dates.
- Modify `hugo.toml`: define English and Chinese list-specific date formats.
- Modify `layouts/_partials/post-list.html`: select the list-specific format with backward-compatible fallback.

### Task 1: Localize grouped-list row dates without years

**Files:**
- Modify: `tests/test_site.py`
- Modify: `hugo.toml:62-99`
- Modify: `layouts/_partials/post-list.html:2-42`

- [ ] **Step 1: Write a failing generated-site test**

Add this method to `GeneratedSiteTests` in `tests/test_site.py`:

```python
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
                    '<time datetime="2026-08-08">August 8</time>', html
                )
                self.assertNotIn(
                    '<time datetime="2026-08-08">August 8, 2026</time>',
                    html,
                )
                self.assertIn(
                    '<li class="post-year" data-post-year="2026">', html
                )
            self.assertIn(
                '<time datetime="2026-08-09">August 9</time>',
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
                    '<li class="post-year" data-post-year="2026">', html
                )
            self.assertIn(
                '<time datetime="2026-08-09">8月9日</time>',
                chinese_tag,
            )

            self.assertIn(
                '<time datetime="2026-08-08">Published August 8, 2026</time>',
                english_article,
            )
            self.assertIn(
                '<time datetime="2026-08-08">发布于2026年8月8日</time>',
                chinese_article,
            )
```

This covers both callers, both languages, both base-path shapes, retained year headings and ISO attributes, and unchanged article dates.

- [ ] **Step 2: Run the new test and verify RED**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_grouped_lists_use_localized_dates_without_repeating_year -v
```

Expected: FAIL because list rows still render `August 8, 2026` and `2026年8月8日`.

- [ ] **Step 3: Add language-local list formats**

In English language params in `hugo.toml`, keep the full format and add:

```toml
dateFormat = ":date_long"
listDateFormat = "January 2"
```

In Chinese language params, keep the full format and add:

```toml
dateFormat = ":date_long"
listDateFormat = "1月2日"
```

- [ ] **Step 4: Use the list format in the shared partial**

After `$page` in `layouts/_partials/post-list.html`, derive the row format with the full format as fallback:

```go-html-template
{{ $dateFormat := default $page.Site.Params.dateFormat $page.Site.Params.listDateFormat }}
```

Change only the visible contents of the row `<time>` element:

```go-html-template
<time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date | time.Format $dateFormat }}</time>
```

Do not change the ISO `datetime`, year metadata/grouping, ordering, article partial, RSS, sitemap, or search module.

- [ ] **Step 5: Run focused GREEN verification**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_grouped_lists_use_localized_dates_without_repeating_year -v
```

Expected: one test PASS, including all English/Chinese and root/project subtests.

- [ ] **Step 6: Run the complete regression gate**

Run:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
python3 -B scripts/validate_interaction_ids.py content
node --check assets/js/post-search.mjs
node --check assets/js/kudos.mjs
node --check assets/js/popular-posts.mjs
actionlint .github/workflows/hugo.yml
```

Expected: 88 Python tests PASS, 59 Node tests PASS, and all remaining commands exit zero.

Build and check both URL shapes:

```bash
LIST_ROOT_BUILD="$(mktemp -d)"
LIST_SUBPATH_BUILD="$(mktemp -d)"
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.test/ --destination "$LIST_ROOT_BUILD"
python3 scripts/check_site.py "$LIST_ROOT_BUILD" --base-url https://example.test/
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.test/example-blog/ \
  --destination "$LIST_SUBPATH_BUILD"
python3 scripts/check_site.py "$LIST_SUBPATH_BUILD" \
  --base-url https://example.test/example-blog/
```

Expected: both builds exit zero without warnings and both checkers print `base-path verification passed`. Remove only those two temporary directories afterward.

- [ ] **Step 7: Self-review and commit**

Confirm the diff changes only list-date configuration, the visible shared row format, and tests. Verify `layouts/_partials/article.html`, RSS, sitemaps, content, and the vendored theme are unchanged.

```bash
git add tests/test_site.py hugo.toml layouts/_partials/post-list.html
git diff --cached --check
git diff --cached --name-only
git commit -m "refactor: omit years from grouped-list dates"
```

Expected staged paths, exactly:

```text
hugo.toml
layouts/_partials/post-list.html
tests/test_site.py
```

### Task 2: Independent review and local integration

**Files:**
- Review only: Task 1 paths and generated output

- [ ] **Step 1: Run an independent specification review**

Compare code and root/subpath output to `docs/superpowers/specs/2026-08-10-year-grouped-list-dates-design.md`. Verify both callers, both languages, complete article/ISO dates, grouping, and exact scope.

- [ ] **Step 2: Run an independent code-quality review**

Review for a clean configuration boundary, correct Hugo `default` semantics, locale correctness, robust generated assertions, fallback behavior, and absence of unrelated changes. Re-run focused tests and generated probes.

- [ ] **Step 3: Fast-forward local main after approval**

Verify both worktrees are clean and `main` is an ancestor of `feat/yearless-list-dates`. Fast-forward local `main`, rerun the complete regression gate, and remove the clean temporary worktree/merged branch. Do not push or stop the user's Hugo server.
