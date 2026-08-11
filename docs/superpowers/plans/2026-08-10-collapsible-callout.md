# Collapsible Callout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render Hugo Markdown alerts as accessible callouts and collapse the Istanbul post’s “My working session” content by default.

**Architecture:** A site-level blockquote render hook maps Hugo alert metadata to either native `<details>` disclosure markup or a visible callout `<div>`, while leaving ordinary blockquotes intact. Site CSS supplies restrained shared presentation, i18n supplies default alert labels, and the Istanbul Markdown opts into the closed state with Hugo’s `-` alert marker.

**Tech Stack:** Hugo/Goldmark render hooks, Go templates, HTML `<details>`/`<summary>`, CSS, TOML i18n, Python `unittest`

---

## File map

- Create `layouts/_markup/render-blockquote.html`: translate Hugo alert metadata into callout or blockquote HTML.
- Modify `assets/css/site.css`: style callouts and add keyboard focus treatment for summaries.
- Modify `i18n/en.toml` and `i18n/zh.toml`: provide localized fallback labels for built-in alert types.
- Modify `tests/fixtures/content/blog/shared-article/index.en.md` and `index.zh.md`: exercise folded, open, unmarked, localized, code-bearing, and plain-quote cases.
- Modify `tests/test_site.py`: verify generic callout behavior and the real Istanbul page contract.
- Modify `content/blog/the-miracle-of-istanbul/index.en.md`: put the existing session command and output inside a folded note.

### Task 1: Complete the reusable callout renderer

**Files:**
- Create: `layouts/_markup/render-blockquote.html`
- Modify: `assets/css/site.css:28-56`
- Modify: `i18n/en.toml:79-88`
- Modify: `i18n/zh.toml:79-88`
- Modify: `tests/fixtures/content/blog/shared-article/index.en.md:22-38`
- Modify: `tests/fixtures/content/blog/shared-article/index.zh.md:17-20`
- Test: `tests/test_site.py:2381-2412`

The worktree already contains the test and candidate implementation for this task. Preserve those edits and validate them before making further changes.

- [ ] **Step 1: Review the generic fixture contract**

Ensure the English fixture contains all four authoring forms:

````markdown
> Plain fixture quote.

> [!NOTE]- Folded fixture callout
>
> ``` r
> folded <- TRUE
> ```

> [!TIP]+ Unfolded fixture callout
>
> Fixture tip body.

> [!WARNING]
>
> Fixture warning body.
````

Ensure the Chinese fixture contains an untitled warning so the default label is localized:

```markdown
> [!WARNING]
>
> 测试警告内容。
```

- [ ] **Step 2: Run the focused generic test**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_callouts_fold_on_the_author_marker_and_localize_their_label -v
```

Expected: `OK`. If it fails, use the rendered assertion difference to make the minimal correction in the files listed for this task.

- [ ] **Step 3: Keep the render hook minimal**

The final hook should distinguish alerts from ordinary quotes, use the explicit title before the localized fallback, and emit `open` only for `+`:

```go-html-template
{{- if eq .Type "alert" -}}
  {{- $label := or .AlertTitle (i18n .AlertType) | default (title .AlertType) -}}
  {{- if .AlertSign -}}
    <details class="callout callout-{{ .AlertType }}"{{ if eq .AlertSign "+" }} open{{ end }}>
      <summary>{{ $label }}</summary>
      {{ .Text }}
    </details>
  {{- else -}}
    <div class="callout callout-{{ .AlertType }}">
      <p class="callout-label">{{ $label }}</p>
      {{ .Text }}
    </div>
  {{- end -}}
{{- else -}}
  <blockquote>{{ .Text }}</blockquote>
{{- end -}}
```

- [ ] **Step 4: Keep the CSS and translations scoped**

The CSS must use the site’s existing tokens, add `summary:focus-visible` to the shared focus rule, show a pointer cursor, and add bottom spacing only while open. Keep English labels `Note`, `Tip`, `Important`, `Warning`, and `Caution`, with Chinese labels `说明`, `提示`, `重要`, `警告`, and `注意`.

- [ ] **Step 5: Re-run the focused test and whitespace check**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_callouts_fold_on_the_author_marker_and_localize_their_label -v
git diff --check
```

Expected: the test reports `OK`; `git diff --check` prints nothing and exits zero.

- [ ] **Step 6: Commit the reusable callout support**

```bash
git add layouts/_markup/render-blockquote.html assets/css/site.css i18n/en.toml i18n/zh.toml tests/fixtures/content/blog/shared-article/index.en.md tests/fixtures/content/blog/shared-article/index.zh.md tests/test_site.py
git commit -m "feat: add collapsible Markdown callouts"
```

### Task 2: Fold the Istanbul working-session section

**Files:**
- Modify: `tests/test_site.py:2414`
- Modify: `content/blog/the-miracle-of-istanbul/index.en.md:596-636`

- [ ] **Step 1: Add a failing real-content regression test**

Add this test next to the generic callout test:

```python
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
    self.assertIn("sessionInfo()", callout.group(2))
    self.assertIn("R version 4.1.0", callout.group(2))
```

- [ ] **Step 2: Run the new test to verify it fails**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_istanbul_working_session_is_folded_by_default -v
```

Expected: `FAIL` because the page has no `callout-note` details element yet.

- [ ] **Step 3: Convert the heading and preserve the body**

Replace the `## My working session` heading with:

````markdown
> [!NOTE]- My working session
>
> ``` r
> sessionInfo()
> ```
>
>     ## R version 4.1.0 (2021-05-18)
````

Continue prefixing every existing session-output line through `compiler_4.1.0` with `> `, including the blank quoted lines. Do not change the command or output text. Leave `## Source code` outside the alert.

- [ ] **Step 4: Run the content and generic callout tests**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_istanbul_working_session_is_folded_by_default \
  tests.test_site.GeneratedSiteTests.test_callouts_fold_on_the_author_marker_and_localize_their_label \
  -v
```

Expected: both tests pass and the command reports `OK`.

- [ ] **Step 5: Commit the folded Istanbul section**

```bash
git add content/blog/the-miracle-of-istanbul/index.en.md tests/test_site.py
git commit -m "content: fold Istanbul working session"
```

### Task 3: Verify the complete site

**Files:**
- Verify only; no planned modifications.

- [ ] **Step 1: Run the full Python suite**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: all tests pass with final status `OK`.

- [ ] **Step 2: Run the production Hugo build**

Run:

```bash
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings --baseURL http://localhost:1313/
```

Expected: Hugo exits zero with no warnings or errors.

- [ ] **Step 3: Run workflow and diff checks**

Run:

```bash
actionlint .github/workflows/hugo.yml
git diff --check
git status --short
```

Expected: `actionlint` and `git diff --check` exit zero. `git status --short` shows no uncommitted callout/content changes; unrelated pre-existing user changes, if any, remain untouched.
