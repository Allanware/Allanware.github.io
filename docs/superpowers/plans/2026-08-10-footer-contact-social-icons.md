# Footer Contact and Profile Icons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the contact link off the home page into a footer row that also links GitHub and Google Scholar, rendering all three as 16px icons beside the existing RSS sentence.

**Architecture:** A rewritten `layouts/_partials/footer.html` emits a centered flex row: an inline `currentColor` envelope SVG, two `<img>` brand marks sourced from `assets/images/`, and the unchanged subscribe sentence. Destinations live in `hugo.toml` parameters; accessible names live in the two i18n files. The GitHub mark is a black roundel, so the dark scheme inverts it with a single CSS filter rule rather than editing the asset.

**Tech Stack:** Hugo 0.164.0 extended (asset pipeline, `resources.Get`, `.Resize`, `fingerprint`), Python `unittest` against generated HTML, plain CSS in `assets/css/site.css`.

## Global Constraints

- Hugo builds run `--panicOnWarning` and `--printI18nWarnings`: every `T` key used must exist in **both** `i18n/en.toml` and `i18n/zh.toml`, or the build fails.
- `layouts/_partials/footer.html` must keep a provenance comment containing both `f5c57c5ea39a091f0167af6312f4d4e385df2e6c` and `layouts/partials/footer.html` — asserted by `tests/test_repository.py:157-161`.
- Do **not** modify `[params.author]` in `hugo.toml`; the vendored RSS template depends on that path (noted in the file's own comment).
- Declarations inside each `assets/css/site.css` rule are ordered alphabetically. Follow that.
- Do **not** place a `:root` block inside any new `@media (prefers-color-scheme: dark)` in `site.css`. `css_root_custom_properties` (`tests/test_site.py:113-136`) matches the first such block and would fold stray tokens into the contrast test at `tests/test_site.py:2847`.
- The theme base stylesheet styles every `img` with `border: 1px solid var(--border-color)`, `border-radius: 4px`, and `margin-left/right: auto` (`themes/hugo-bearneo/layouts/partials/style.html:144-152`). Footer icons must override border, border-radius, and margin.
- Icons render at **16px**; the Scholar source is resized to **32px** for a 2x pixel ratio.
- Footer row order is fixed: contact, GitHub, Scholar, RSS.
- Accessible names — EN: `Contact`, `GitHub`, `Google Scholar`. ZH: `联系`, `GitHub`, `谷歌学术`.
- The mail address must never appear as visible text, only inside a `mailto:` href.
- Destination URLs: `mailto:xiaodoubizwx@gmail.com`, `https://github.com/Allanware`, `https://scholar.google.com/citations?user=cd-oBQUAAAAJ`.

**Verification commands:**

```bash
# Single test
python3 -m unittest tests.test_site.GeneratedSiteTests.<test_name> -v
# Full gate
python3 scripts/validate_interaction_ids.py content
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
actionlint .github/workflows/hugo.yml
```

---

### Task 1: Footer icon row

Adds the three links, their assets, parameters, and translations. Ordered before the home-page change so the site never has a commit with no contact link at all.

**Files:**
- Create: `assets/images/github-logo.svg` (moved from `github_logo.svg` at repo root)
- Create: `assets/images/google-scholar-logo.webp` (moved from `Google_Scholar_logo.webp` at repo root)
- Modify: `layouts/_partials/footer.html` (full rewrite, 4 lines)
- Modify: `hugo.toml:52-58` (the `[params]` block)
- Modify: `i18n/en.toml`, `i18n/zh.toml` (append three keys)
- Test: `tests/test_site.py:2825-2845` (footer block of `test_chrome_is_localized_and_uses_browser_color_preference`)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: CSS class names that Task 3 styles — `footer-links` (row container), `footer-link` (each anchor), `footer-icon` (all three icons), `footer-icon-github` (GitHub mark only), `footer-subscribe` (RSS sentence wrapper). Site parameters `contactEmail`, `githubURL`, `scholarURL`. i18n keys `contact`, `github`, `googleScholar`.

- [ ] **Step 1: Write the failing test**

In `tests/test_site.py`, replace the footer loop at the end of `test_chrome_is_localized_and_uses_browser_color_preference` (currently `tests/test_site.py:2825-2845`, beginning `for language, html, rss_path, removed_text in (`) with:

```python
            for (
                language,
                html,
                rss_path,
                contact_label,
                scholar_label,
                subscribe_text,
                removed_text,
            ) in (
                (
                    "en",
                    english,
                    "/index.xml",
                    "Contact",
                    "Google Scholar",
                    "Subscribe via",
                    ("Made with", "Hugo Bear Neo", "Sitemap"),
                ),
                (
                    "zh",
                    chinese,
                    "/zh/index.xml",
                    "联系",
                    "谷歌学术",
                    "订阅",
                    ("网站主题", "Hugo Bear Neo", "网站地图"),
                ),
            ):
                footer = re.search(r"<footer>(.*?)</footer>", html, re.DOTALL)
                self.assertIsNotNone(footer)
                with self.subTest(language=language):
                    markup = footer.group(1)
                    self.assertEqual(4, markup.count("<a "))
                    self.assertEqual(
                        [
                            "mailto:xiaodoubizwx@gmail.com",
                            "https://github.com/Allanware",
                            "https://scholar.google.com/citations?user=cd-oBQUAAAAJ",
                            rss_path,
                        ],
                        re.findall(r'<a\b[^>]*\bhref="([^"]+)"', markup),
                    )
                    self.assertIn(f'aria-label="{contact_label}"', markup)
                    self.assertIn('alt="GitHub"', markup)
                    self.assertIn(f'alt="{scholar_label}"', markup)
                    self.assertEqual(
                        3, len(re.findall(r'width="16" height="16"', markup))
                    )
                    self.assertIn(subscribe_text, markup)
                    self.assertNotRegex(
                        markup, r">[^<]*xiaodoubizwx@gmail\.com[^<]*<"
                    )
                    for text in removed_text:
                        self.assertNotIn(text, markup)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_site.GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference -v`

Expected: FAIL with `AssertionError: 4 != 1` (the footer currently holds only the RSS link).

- [ ] **Step 3: Move the two logo assets into the pipeline**

The files are untracked at the repo root, so `git mv` does not apply — plain `mv`, then stage:

```bash
mv github_logo.svg assets/images/github-logo.svg
mv Google_Scholar_logo.webp assets/images/google-scholar-logo.webp
```

- [ ] **Step 4: Register the three destinations as site parameters**

In `hugo.toml`, append to the existing `[params]` block, immediately after `externalLinksNewTab = false` and **before** the `[params.giscus]` sub-table. Leave `[params.author]` untouched.

```toml
  contactEmail = "xiaodoubizwx@gmail.com"
  githubURL = "https://github.com/Allanware"
  scholarURL = "https://scholar.google.com/citations?user=cd-oBQUAAAAJ"
```

- [ ] **Step 5: Add the accessible names to both translation files**

Append to `i18n/en.toml`:

```toml
[contact]
other = "Contact"
[github]
other = "GitHub"
[googleScholar]
other = "Google Scholar"
```

Append to `i18n/zh.toml`:

```toml
[contact]
other = "联系"
[github]
other = "GitHub"
[googleScholar]
other = "谷歌学术"
```

- [ ] **Step 6: Rewrite the footer partial**

Replace the entire contents of `layouts/_partials/footer.html` with:

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/partials/footer.html; site-local contact and profile icons. */ -}}
{{- $githubSource := resources.Get "images/github-logo.svg" -}}
{{- if not $githubSource -}}
  {{- errorf "required footer icon assets/images/github-logo.svg is missing" -}}
{{- end -}}
{{- $scholarSource := resources.Get "images/google-scholar-logo.webp" -}}
{{- if not $scholarSource -}}
  {{- errorf "required footer icon assets/images/google-scholar-logo.webp is missing" -}}
{{- end -}}
{{- $github := $githubSource | fingerprint "sha256" -}}
{{- $scholar := $scholarSource.Resize "32x32 webp Lanczos" -}}
<div class="footer-links">
  {{- with .Site.Params.contactEmail -}}
    <a class="footer-link" href="mailto:{{ . }}" aria-label="{{ T "contact" }}">
      <svg class="footer-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true" focusable="false">
        <path d="M2 5.5A1.5 1.5 0 0 1 3.5 4h17A1.5 1.5 0 0 1 22 5.5V6l-10 6.5L2 6V5.5Z"></path>
        <path d="M2 8.2l10 6.3 10-6.3V18.5A1.5 1.5 0 0 1 20.5 20h-17A1.5 1.5 0 0 1 2 18.5V8.2Z"></path>
      </svg>
    </a>
  {{- end -}}
  {{- with .Site.Params.githubURL -}}
    <a class="footer-link" href="{{ . }}" rel="me">
      <img class="footer-icon footer-icon-github" src="{{ $github.RelPermalink }}" width="16" height="16" alt="{{ T "github" }}" loading="lazy" decoding="async">
    </a>
  {{- end -}}
  {{- with .Site.Params.scholarURL -}}
    <a class="footer-link" href="{{ . }}" rel="me">
      <img class="footer-icon" src="{{ $scholar.RelPermalink }}" width="16" height="16" alt="{{ T "googleScholar" }}" loading="lazy" decoding="async">
    </a>
  {{- end -}}
  {{- with .Site.Home.OutputFormats.Get "RSS" -}}
    <span class="footer-subscribe">{{ T "subscribeVia" }} <a href="{{ .RelPermalink }}">{{ T "rss" }}</a>.</span>
  {{- end -}}
</div>
```

Notes for the implementer:
- The envelope is two adjacent filled subpaths — a flap wedge and a body with a matching V dip. The hairline between them reads as the flap seam. No `fill-rule` tricks, no holes.
- `.Site.Home.OutputFormats.Get "RSS"` resolves per-language, which is what produces `/zh/index.xml`. Keep it at the partial's outer scope, not nested inside another `with`, or `.` will be rebound.
- `alt` on an `<img>` that is an anchor's only content becomes that anchor's accessible name, so the two brand links need no `aria-label`.

- [ ] **Step 7: Run test to verify it passes**

Run: `python3 -m unittest tests.test_site.GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference -v`

Expected: PASS.

- [ ] **Step 8: Run the full gate**

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
```

Expected: all pass. `test_localized_brand_contact_and_generated_favicons` still passes at this point — the home page keeps its link until Task 2.

- [ ] **Step 9: Commit**

```bash
git add assets/images/github-logo.svg assets/images/google-scholar-logo.webp \
  layouts/_partials/footer.html hugo.toml i18n/en.toml i18n/zh.toml tests/test_site.py
git commit -m "feat: add footer contact and profile icons"
```

---

### Task 2: Home introduction without the contact link

**Files:**
- Modify: `content/_index.en.md:5`
- Modify: `content/_index.zh.md:5`
- Test: `tests/test_site.py:2126-2135` (inside `test_localized_brand_contact_and_generated_favicons`)

**Interfaces:**
- Consumes: nothing. The footer link from Task 1 is what makes this removal safe, but no code dependency exists.
- Produces: nothing consumed later.

- [ ] **Step 1: Write the failing test**

In `tests/test_site.py`, inside `test_localized_brand_contact_and_generated_favicons`, replace these two assertions (currently `tests/test_site.py:2126-2135`):

```python
                self.assertIn(
                    '<p>Wenxuan Zhao. <a href="mailto:xiaodoubizwx@gmail.com">Contact me</a>.</p>',
                    english,
                )
```

and

```python
                self.assertIn(
                    '<p>赵文轩。<a href="mailto:xiaodoubizwx@gmail.com">联系我</a>。</p>',
                    chinese,
                )
```

with, respectively:

```python
                self.assertIn("<p>Wenxuan Zhao.</p>", english)
```

and

```python
                self.assertIn("<p>赵文轩。</p>", chinese)
```

Then, directly after the `chinese` assertion, add a check that the introduction carries no link at all in either language:

```python
                for language, html in (("en", english), ("zh", chinese)):
                    intro = re.search(
                        r'<div class="home-intro">(.*?)</div>', html, re.DOTALL
                    )
                    self.assertIsNotNone(intro, language)
                    with self.subTest(build=name, language=language):
                        self.assertNotIn("<a ", intro.group(1))
                        self.assertNotIn("mailto:", intro.group(1))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_site.GeneratedSiteTests.test_localized_brand_contact_and_generated_favicons -v`

Expected: FAIL — `'<p>Wenxuan Zhao.</p>' not found`, because the paragraph still contains the mail link.

- [ ] **Step 3: Remove the link from both home introductions**

`content/_index.en.md` becomes:

```markdown
+++
title = "Where Was I"
+++

Wenxuan Zhao.
```

`content/_index.zh.md` becomes:

```markdown
+++
title = "说哪儿了"
+++

赵文轩。
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_site.GeneratedSiteTests.test_localized_brand_contact_and_generated_favicons -v`

Expected: PASS.

- [ ] **Step 5: Run the full gate**

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add content/_index.en.md content/_index.zh.md tests/test_site.py
git commit -m "refactor: move home contact link into the footer"
```

---

### Task 3: Footer row layout and dark-scheme handling

**Files:**
- Modify: `assets/css/site.css` (append)
- Test: `tests/test_site.py` (site_css assertions in `test_chrome_is_localized_and_uses_browser_color_preference`)

**Interfaces:**
- Consumes: the class names Task 1 produced — `footer-links`, `footer-link`, `footer-icon`, `footer-icon-github`.
- Produces: nothing consumed later.

- [ ] **Step 1: Write the failing test**

In `tests/test_site.py`, inside `test_chrome_is_localized_and_uses_browser_color_preference`, add these three assertions immediately after the existing `.language-switcher` margin/padding `assertRegex` block and before the `for language, html, rss_path, ...` footer loop:

```python
            self.assertRegex(
                site_css,
                r"\.footer-links\s*\{[^}]*align-items:\s*center;"
                r"[^}]*display:\s*flex;"
                r"[^}]*flex-wrap:\s*wrap;"
                r"[^}]*justify-content:\s*center;[^}]*\}",
            )
            self.assertRegex(
                site_css,
                r"\.footer-icon\s*\{[^}]*border:\s*0;"
                r"[^}]*height:\s*16px;"
                r"[^}]*margin:\s*0;"
                r"[^}]*width:\s*16px;[^}]*\}",
            )
            self.assertRegex(
                site_css,
                r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{\s*"
                r"\.footer-icon-github\s*\{[^}]*filter:\s*invert\(1\);[^}]*\}",
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_site.GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference -v`

Expected: FAIL — `Regex didn't match` for the `.footer-links` rule.

- [ ] **Step 3: Add the styles**

Append to `assets/css/site.css`. Declarations stay alphabetical within each rule; the icon rule overrides the theme's global `img` border, radius, and auto margins.

```css
.footer-links {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
}

.footer-link {
  display: inline-flex;
  line-height: 1;
}

.footer-icon {
  border: 0;
  border-radius: 0;
  display: block;
  height: 16px;
  margin: 0;
  width: 16px;
}

@media (prefers-color-scheme: dark) {
  .footer-icon-github {
    filter: invert(1);
  }
}
```

The supplied GitHub art is a black roundel enclosing a white octocat, so `invert(1)` yields a white roundel enclosing a dark octocat — the conventional dark-scheme treatment. The Scholar mark keeps its brand blue in both schemes and must **not** be inverted, which is why the filter is scoped to `.footer-icon-github`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_site.GeneratedSiteTests.test_chrome_is_localized_and_uses_browser_color_preference -v`

Expected: PASS.

- [ ] **Step 5: Run the full gate, including a production build and link check**

```bash
python3 scripts/validate_interaction_ids.py content
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
actionlint .github/workflows/hugo.yml
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings --baseURL https://example.org/
python3 scripts/check_site.py public --base-url https://example.org/
```

Expected: all green. The production build must emit no i18n warnings, which confirms all three keys resolve in both languages.

- [ ] **Step 6: Commit**

```bash
git add assets/css/site.css tests/test_site.py
git commit -m "style: lay out the footer icon row"
```

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task |
| --- | --- |
| Home keeps the name, drops the mail link | 2 |
| Footer row: three icons then the subscribe sentence | 1 |
| Row wraps on narrow viewports | 3 |
| 16px icons, 32px Scholar source | 1 (markup, resize), 3 (sizing) |
| Localized accessible names, no visible icon text | 1 |
| Mail address absent from visible text | 1 (footer), 2 (home) |
| RSS wording, trailing period, last position | 1 |
| Assets relocated under kebab-case names | 1 |
| Three parameters, `[params.author]` untouched | 1 |
| Inline `currentColor` envelope, filled | 1 |
| GitHub via `<img>` plus dark-scheme inversion | 1 (markup), 3 (filter) |
| Scholar resized, unfiltered | 1 (resize), 3 (scoped filter) |
| `errorf` guards on both lookups | 1 |
| Exactly four footer links, in order | 1 |
| Upstream attribution text stays absent | 1 (retained `removed_text` loop) |
| Full suite, validator, actionlint, strict builds green | 3 |

**Placeholder scan:** none — every step carries the literal content to apply.

**Type consistency:** the five class names in Task 1's markup (`footer-links`, `footer-link`, `footer-icon`, `footer-icon-github`, `footer-subscribe`) match Task 3's selectors; `footer-subscribe` and `footer-link` are deliberately styled only where needed. Parameter names `contactEmail`/`githubURL`/`scholarURL` and i18n keys `contact`/`github`/`googleScholar` are identical in the config, template, and test steps.
