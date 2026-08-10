# Individual Tag Page Presentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify individual English and Chinese tag pages to use `Tag:` headings, omit the tag-overview backlink, and hide group counts without changing other lists or search accessibility.

**Architecture:** Keep the existing term template and shared post-list partial. Add one optional `ShowCount` input to the partial, default it to the existing global configuration, and disable it only for the two term-page groups. Update localized heading strings and generated-site assertions at both supported base paths.

**Tech Stack:** Hugo 0.164 Go templates, Hugo i18n TOML, Python 3.11+ `unittest`, Node.js 22+ tests.

---

## File map

- Modify `tests/test_site.py`: make the individual-term-page contract executable at root and project-subpath base URLs while preserving overview/archive assertions.
- Modify `layouts/_partials/post-list.html`: accept a per-call visible-count override while retaining existing default behavior.
- Modify `layouts/term.html`: remove the backlink and disable visible counts in both tag groups.
- Modify `i18n/en.toml`: change the heading to `Tag: {{ . }}` and remove the unused `allTags` key.
- Modify `i18n/zh.toml`: change the heading to `标签：{{ . }}` and remove the unused `allTags` key.

### Task 1: Simplify individual tag-term pages

**Files:**
- Modify: `tests/test_site.py:2914-3113`
- Modify: `layouts/_partials/post-list.html:2-26`
- Modify: `layouts/term.html:1-32`
- Modify: `i18n/en.toml:39-42`
- Modify: `i18n/zh.toml:39-42`

- [ ] **Step 1: Write the failing generated-site assertions**

In `GeneratedSiteTests.test_tag_results_group_projects_before_posts`, add exact term-heading and backlink-removal assertions inside the existing root/project build loop:

```python
self.assertIn("<h2>Tag: fixture</h2>", english)
self.assertIn("<h2>标签：测试</h2>", chinese)
self.assertNotIn(">All tags</a>", english)
self.assertNotIn(">全部标签</a>", chinese)
```

After extracting each project/post group, replace the visible count-copy assertions with explicit absence of the visible count element:

```python
for group in (
    english_projects,
    english_posts,
    chinese_projects,
    chinese_posts,
):
    self.assertNotIn("data-post-count", group)
```

Retain all existing content-isolation, search-control, module-cardinality, link, sitemap, and overview-count assertions. Strengthen the ordinary Posts archive assertion so it proves the visible count remains:

```python
self.assertIn("<p data-post-count>1 post</p>", english_blog)
```

For the production visualization term, add:

```python
self.assertIn("<h2>Tag: visualization</h2>", visualization)
self.assertNotIn(">All tags</a>", visualization)
self.assertNotIn("data-post-count", visualization)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_tag_results_group_projects_before_posts -v
```

Expected: FAIL because the generated pages still contain `Tagged “…”`, the backlink, and `data-post-count`.

- [ ] **Step 3: Add a tag-page-only visible-count override**

In `layouts/_partials/post-list.html`, derive the setting next to the other partial options:

```go-html-template
{{ $showCount := $page.Site.Params.showPostCount }}
{{ if isset . "ShowCount" }}
  {{ $showCount = .ShowCount }}
{{ end }}
```

Use that local value for the visible paragraph:

```go-html-template
{{ if $showCount }}
  <p data-post-count>{{ T $countKey $count }}</p>
{{ end }}
```

Do not remove `data-count-one`, `data-count-many`, or the live status region; the search module needs those accessible announcement templates.

- [ ] **Step 4: Simplify the individual term template**

Delete the `Site.GetPage "/tags"` backlink line from `layouts/term.html`.

Pass the new option to the Projects group:

```go-html-template
"SearchMinimum" 2
"ShowCount" false
"IncludeScript" false
```

Pass it to the Posts group:

```go-html-template
"Page" . "Pages" $posts "SearchMinimum" 2
"ShowCount" false
"IncludeScript" false
```

Keep Projects before Posts and retain the shared module-loading condition.

- [ ] **Step 5: Update both localized headings**

In `i18n/en.toml`, replace the heading and remove the obsolete `allTags` block:

```toml
[filteringFor]
other = "Tag: {{ . }}"
```

In `i18n/zh.toml`, replace the heading and remove the obsolete `allTags` block:

```toml
[filteringFor]
other = "标签：{{ . }}"
```

- [ ] **Step 6: Run focused GREEN verification**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_tag_results_group_projects_before_posts -v
```

Expected: one test PASS, including all root/project and English/Chinese subtests.

- [ ] **Step 7: Run the complete regression gate**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
python3 scripts/validate_interaction_ids.py content
node --check assets/js/post-search.mjs
node --check assets/js/kudos.mjs
node --check assets/js/popular-posts.mjs
actionlint .github/workflows/hugo.yml
```

Expected: 87 Python tests PASS, 59 Node tests PASS, and all remaining commands exit zero.

Build and inspect both URL shapes:

```bash
TAG_ROOT_BUILD="$(mktemp -d)"
TAG_SUBPATH_BUILD="$(mktemp -d)"
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.test/ --destination "$TAG_ROOT_BUILD"
python3 scripts/check_site.py "$TAG_ROOT_BUILD" --base-url https://example.test/
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.test/example-blog/ --destination "$TAG_SUBPATH_BUILD"
python3 scripts/check_site.py "$TAG_SUBPATH_BUILD" \
  --base-url https://example.test/example-blog/
```

Expected: both Hugo builds exit zero with no warnings and both checkers print `base-path verification passed`.

- [ ] **Step 8: Commit the implementation**

```bash
git add tests/test_site.py layouts/_partials/post-list.html layouts/term.html i18n/en.toml i18n/zh.toml
git commit -m "refactor: simplify individual tag pages"
```

Before committing, `git diff --cached --check` must exit zero and the staged paths must be exactly the five files listed above.

### Task 2: Independent review and local integration

**Files:**
- Review only: all Task 1 paths

- [ ] **Step 1: Run an independent specification review**

Confirm the generated behavior matches `docs/superpowers/specs/2026-08-10-tag-term-presentation-design.md`, including localized headings, backlink absence, tag-page-only count suppression, retained search announcements, and unchanged overview/archive counts.

- [ ] **Step 2: Run an independent code-quality review**

Inspect the complete branch diff for accidental global count removal, duplicated list logic, inaccessible search status, untranslated copy, base-path regressions, or unrelated changes. Re-run the focused test and relevant source checks.

- [ ] **Step 3: Fast-forward local main after approval**

Verify both worktrees are clean and `main` is an ancestor of `feat/tag-term-presentation`. Fast-forward local `main`, rerun the complete regression gate on the integrated tree, and remove the clean temporary worktree/merged branch. Do not push or stop the user's Hugo server.
