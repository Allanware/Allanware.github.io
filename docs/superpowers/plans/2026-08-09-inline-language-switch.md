# Inline Language Switch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the single alternate-language link immediately after Home, Posts, and Tags on the same header row, and shorten the Chinese label to `中文`.

**Architecture:** Preserve separate primary and language `<nav>` landmarks, but place them inside one presentational `.header-navigation` flex row. Size the primary navigation to its contents so the language landmark follows Tags instead of consuming the remaining row width. Keep translation availability and linking logic unchanged; CSS prevents the two navigation landmarks from wrapping into separate rows at the supported mobile width.

**Tech Stack:** Hugo 0.164 Go templates, TOML, CSS, Python standard-library generated-site tests, Playwright/Chrome acceptance.

---

**Current state:** Tasks 1 and 2 were completed in `e9b17c7` and `9be9e88`. Task 3's content-sizing change was completed in `00492b2`; execute its balanced-divider additions next.

### Task 1: Render one semantic, non-wrapping navigation row

**Files:**
- Modify: `tests/test_site.py`
- Modify: `layouts/_partials/header.html`
- Modify: `assets/css/site.css`
- Modify: `hugo.toml`

- [ ] **Step 1: Add failing generated-site and stylesheet assertions**

Extend `GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference` in `tests/test_site.py` after the existing language-switcher assertion:

```python
            for language, html, alternate_label in (
                ("en", english, "中文"),
                ("zh", chinese, "English"),
            ):
                row = re.search(
                    r'<div class="header-navigation">(.*?)</div>',
                    html,
                    re.DOTALL,
                )
                self.assertIsNotNone(row)
                with self.subTest(language=language):
                    self.assertEqual(1, row.group(1).count("data-primary-navigation"))
                    self.assertEqual(1, row.group(1).count('class="language-switcher"'))
                    self.assertEqual(1, row.group(1).count("hreflang="))
                    self.assertIn(f">{alternate_label}</a>", row.group(1))

            configuration = tomllib.loads((ROOT / "hugo.toml").read_text())
            self.assertEqual("中文", configuration["languages"]["zh"]["label"])
            site_css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
            self.assertRegex(
                site_css,
                r"\.header-navigation\s*\{[^}]*display:\s*flex;"
                r"[^}]*flex-wrap:\s*nowrap;[^}]*\}",
            )
            self.assertRegex(
                site_css,
                r"\.language-switcher\s*\{[^}]*display:\s*inline-flex;"
                r"[^}]*white-space:\s*nowrap;[^}]*\}",
            )
```

In the existing unpaired-post assertion within `test_root_and_project_subpath_production_matrix_is_complete`, retain `self.assertNotIn("language-switcher", beyond)` and add:

```python
                    self.assertEqual(1, beyond.count('class="header-navigation"'))
```

- [ ] **Step 2: Run the focused tests and observe the required failure**

Run:

```bash
python3 -m unittest -v \
  tests.test_site.GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference \
  tests.test_site.GeneratedSiteTests.test_root_and_project_subpath_production_matrix_is_complete
```

Expected: FAIL because `.header-navigation` does not exist and the configured Chinese label is still `简体中文`.

- [ ] **Step 3: Group the two navigation landmarks without merging them**

Change `layouts/_partials/header.html` so the navigation portion is:

```go-html-template
<div class="header-navigation">
  <nav aria-label="{{ T "primaryNavigation" }}" data-primary-navigation>
    {{ partial "nav.html" . }}
  </nav>
  {{- $currentPage := . -}}
  {{- $visibleTranslations := where .AllTranslations "Params.hidden" "ne" true -}}
  {{- if and (ge (len $visibleTranslations) 2) (ne .Kind "term") }}
    <nav class="language-switcher" aria-label="{{ T "languageNavigation" }}">
      {{- range $visibleTranslations }}
        {{- if ne .RelPermalink $currentPage.RelPermalink }}
          <a href="{{ .RelPermalink }}" hreflang="{{ .Language.Locale }}" lang="{{ .Language.Locale }}" aria-label="{{ T "switchLanguageTo" .Language.Label }}">{{ .Language.Label }}</a>
        {{- end }}
      {{- end }}
    </nav>
  {{- end }}
</div>
```

Do not add the alternate-language link to the primary menu and do not render a current-language label.

- [ ] **Step 4: Add the non-wrapping row styles**

Add this block before `[data-primary-navigation]` in `assets/css/site.css`:

```css
.header-navigation {
  align-items: baseline;
  display: flex;
  flex-wrap: nowrap;
  max-width: 100%;
}
```

Change the existing primary-navigation block to keep its links together:

```css
[data-primary-navigation] {
  align-items: baseline;
  display: flex;
  flex: 0 1 auto;
  flex-wrap: nowrap;
  gap: 0.5rem;
  min-width: 0;
}
```

Extend `.language-switcher` without changing its separator:

```css
.language-switcher {
  align-items: baseline;
  border-left: 1px solid var(--border-color);
  display: inline-flex;
  flex: 0 0 auto;
  margin-left: 0.5rem;
  padding-left: 0.5rem;
  white-space: nowrap;
}
```

- [ ] **Step 5: Shorten only the Chinese language label**

Change `hugo.toml` under `[languages.zh]`:

```toml
label = "中文"
```

Keep `locale = "zh-CN"`, the Chinese title, URLs, and all English settings unchanged.

- [ ] **Step 6: Run focused and complete automated verification**

Run:

```bash
python3 -m unittest -v \
  tests.test_site.GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference \
  tests.test_site.GeneratedSiteTests.test_root_and_project_subpath_production_matrix_is_complete
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
```

Expected: 71 Python tests and 35 Node tests PASS.

### Task 2: Verify actual desktop and mobile layout

**Files:**
- Verify: generated site only
- Modify only if the browser check exposes a concrete defect

- [ ] **Step 1: Build a local browser fixture**

Run a warning-fatal build with a writable temporary cache and a loopback base URL:

```bash
BLOG_NAV_BUILD="$(mktemp -d)"
BLOG_NAV_CACHE="$(mktemp -d)"
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --environment production --printI18nWarnings --printPathWarnings \
  --cacheDir "$BLOG_NAV_CACHE" --baseURL http://127.0.0.1:1313/ \
  --destination "$BLOG_NAV_BUILD"
```

Serve that directory only on `127.0.0.1:1313` for the browser check.

- [ ] **Step 2: Check row geometry and overflow in Chrome**

At 1280×900 and 390×844, open `/` and `/zh/` and assert:

```javascript
const primary = document.querySelector("[data-primary-navigation]").getBoundingClientRect();
const language = document.querySelector(".language-switcher").getBoundingClientRect();
const lastPrimaryLink = document.querySelector("[data-primary-navigation] a:last-child").getBoundingClientRect();
const languageLink = document.querySelector(".language-switcher a").getBoundingClientRect();
const sameRow = Math.abs(primary.top - language.top) <= 1;
const adjacencyGap = languageLink.left - lastPrimaryLink.right;
const noOverflow = document.documentElement.scrollWidth <= document.documentElement.clientWidth;
const languageLinks = document.querySelectorAll(".language-switcher a").length;
```

Expected: `sameRow === true`, `0 <= adjacencyGap <= 24`, `noOverflow === true`, and `languageLinks === 1` for both languages at both viewport sizes. The English page link text is `中文`; the Chinese page link text is `English`.

Open `/p/beyond-the-cloud/` and confirm `.language-switcher` is absent while the three primary links remain in `.header-navigation`.

- [ ] **Step 3: Run final build and repository checks**

Run:

```bash
actionlint .github/workflows/hugo.yml
python3 scripts/validate_interaction_ids.py content
python3 scripts/check_site.py "$BLOG_NAV_BUILD" --base-url http://127.0.0.1:1313/
git diff --check
```

Expected: every command exits 0.

- [ ] **Step 4: Commit the implementation if Git is authorized**

```bash
git add assets/css/site.css hugo.toml layouts/_partials/header.html tests/test_site.py \
  docs/superpowers/plans/2026-08-09-inline-language-switch.md \
  docs/superpowers/specs/2026-08-09-inline-language-switch-design.md
git commit -m "style: keep language switch inline"
```

### Task 3: Keep the language link adjacent to Tags with a balanced divider

**Files:**
- Modify: `tests/test_site.py`
- Modify: `assets/css/site.css`

- [ ] **Step 1: Add a failing balanced-divider assertion**

Retain this existing primary-navigation sizing assertion in `GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference`:

```python
            self.assertRegex(
                site_css,
                r"\[data-primary-navigation\]\s*\{[^}]*"
                r"flex:\s*0\s+1\s+auto;[^}]*\}",
            )
```

Extend the existing `.language-switcher` source assertion to require equal divider spacing:

```python
            self.assertRegex(
                site_css,
                r"\.language-switcher\s*\{[^}]*"
                r"margin-left:\s*0\.5rem;[^}]*"
                r"padding-left:\s*0\.5rem;[^}]*\}",
            )
```

- [ ] **Step 2: Run the focused test and observe the required failure**

Run:

```bash
python3 -m unittest -v \
  tests.test_site.GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference
```

Expected: FAIL because the divider still uses unequal `0.25rem` and `0.75rem` spacing.

- [ ] **Step 3: Retain content-sized primary navigation and balance the divider**

In `assets/css/site.css`, change only the flex shorthand in the existing primary-navigation block:

```css
[data-primary-navigation] {
  align-items: baseline;
  display: flex;
  flex: 0 1 auto;
  flex-wrap: nowrap;
  gap: 0.5rem;
  min-width: 0;
}
```

Keep the separate navigation landmarks, divider, translation rules, and link labels unchanged.

In the existing `.language-switcher` block, preserve the divider and its total spacing but distribute that space equally:

```css
.language-switcher {
  align-items: baseline;
  border-left: 1px solid var(--border-color);
  display: inline-flex;
  flex: 0 0 auto;
  margin-left: 0.5rem;
  padding-left: 0.5rem;
  white-space: nowrap;
}
```

- [ ] **Step 4: Run focused and complete automated verification**

Run:

```bash
python3 -m unittest -v \
  tests.test_site.GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
```

Expected: 71 Python tests and 35 Node tests PASS.

- [ ] **Step 5: Repeat browser geometry acceptance**

At 1280×900 and 390×844 on `/`, `/zh/`, `/example-blog/`, and `/example-blog/zh/`, compute `adjacencyGap` using the Task 2 geometry snippet.

Expected: both navigation landmarks remain on the same row, `0 <= adjacencyGap <= 24` pixels, computed left margin and padding are equal, there is no document-level horizontal overflow, and each translated page contains exactly one alternate-language link. The untranslated Beyond post retains only the three primary links.

- [ ] **Step 6: Commit the refinement**

```bash
git add assets/css/site.css tests/test_site.py \
  docs/superpowers/plans/2026-08-09-inline-language-switch.md \
  docs/superpowers/specs/2026-08-09-inline-language-switch-design.md
git commit -m "style: keep language switch beside tags"
```
