# Train of Thought Homepage Ending Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rejected thought-balloon homepage ending with a cute, one-shot toy train that reveals `there goes my train of thought.` / `思绪又飘走了。` after it leaves.

**Architecture:** Keep the existing homepage-only partial, fingerprinted ES module, IntersectionObserver state machine, and start-over replay contract. Replace only the partial's decorative SVG and localized line, then rewrite the isolated CSS state styles so a clipped runner crosses once before the caption and return link fade in. Generated-site tests own the markup/localization contract, the CSS source test owns the motion and reduced-motion contract, and the existing Node tests continue to own viewport and replay behavior.

**Tech Stack:** Hugo templates and i18n catalogs, inline SVG, CSS keyframes, dependency-free ES modules, Python `unittest`, Node's built-in test runner.

---

## File Structure

- Modify `tests/test_site.py`: replace balloon-specific generated markup and CSS assertions with the selected train contract.
- Modify `layouts/_partials/home-ending.html`: render the decorative toy-train lane, readable localized caption, and existing return link.
- Modify `i18n/en.toml`: replace the unfinished-thought copy with the English train-of-thought line and remove the unused lead key.
- Modify `i18n/zh.toml`: use `思绪又飘走了。` and remove the unused lead key.
- Modify `assets/css/site.css`: replace balloon styles and keyframes with the clipped train journey, delayed caption, fallback states, and reduced-motion composition.
- Modify `tests/home-ending.test.mjs`: rename the replay test to describe the train while preserving the already-correct generic state-machine assertions.

### Task 1: Lock the train markup and localization contract

**Files:**
- Modify: `tests/test_site.py:1891-2000`
- Modify: `layouts/_partials/home-ending.html:1-12`
- Modify: `i18n/en.toml:89-94`
- Modify: `i18n/zh.toml:89-94`

- [ ] **Step 1: Write the failing generated-site test**

Rename the test to `test_train_of_thought_is_localized_home_only_and_base_path_safe`, change `expected` to:

```python
expected = {
    "en": (
        "there goes my train of thought.",
        "↑ perhaps start over",
    ),
    "zh": (
        "思绪又飘走了。",
        "↑ 要不从头再来",
    ),
}
```

Replace the balloon assertions inside the per-language loop with:

```python
self.assertIn(
    f'<p class="home-ending-caption">{thought}</p>',
    ending,
)
self.assertEqual(1, ending.count("data-home-ending-train"))
self.assertNotIn("data-home-ending-balloon", ending)
self.assertNotIn("data-home-ending-dot", ending)
self.assertRegex(
    ending,
    r'<svg\b(?=[^>]*\bdata-home-ending-train(?:\s|>))'
    r'(?=[^>]*\bviewBox="0 0 132 52")'
    r'(?=[^>]*\bwidth="132")'
    r'(?=[^>]*\bheight="52")'
    r'(?=[^>]*\baria-hidden="true")'
    r'(?=[^>]*\bfocusable="false")[^>]*>',
)
self.assertEqual(1, ending.count("data-home-ending-carriage"))
self.assertEqual(1, ending.count("data-home-ending-engine"))
self.assertEqual(2, ending.count("data-home-ending-smoke"))
self.assertEqual(4, ending.count("data-home-ending-wheel"))
self.assertLess(
    ending.index("data-home-ending-train"),
    ending.index(thought),
)
```

Remove the old `aria-label` assertion because the visible caption now carries the complete localized meaning. Keep all existing assertions for the home-top fragment, return labels, Popular-post ordering, non-home exclusion, lack of bitmap/looping media, module fingerprint/integrity, and both root and project-subpath builds.

- [ ] **Step 2: Run the focused test and verify the red state**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_train_of_thought_is_localized_home_only_and_base_path_safe -v
```

Expected: FAIL because the generated homepage still contains `There was one more thing...` / `好像还有件事……` and `data-home-ending-balloon`.

- [ ] **Step 3: Replace the partial with the train composition**

Use this complete partial while retaining the existing fingerprinted module include:

```html
<div class="home-ending" data-home-ending data-home-ending-state="static">
  <div class="home-ending-lane" aria-hidden="true">
    <div class="home-ending-train-runner">
      <svg class="home-ending-train" data-home-ending-train viewBox="0 0 132 52" width="132" height="52" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <circle data-home-ending-smoke cx="101" cy="6" r="3"></circle>
        <circle data-home-ending-smoke cx="91" cy="3.5" r="2"></circle>
        <rect data-home-ending-carriage x="7" y="20" width="40" height="18" rx="4"></rect>
        <path d="M12 20v-5h30v5M47 33h10"></path>
        <g data-home-ending-engine>
          <path d="M58 38V10h22v28"></path>
          <rect x="63" y="15" width="12" height="9" rx="1.5"></rect>
          <path d="M80 21h31c7.2 0 13 5.8 13 13v4H80V21Z"></path>
          <path d="M99 21V10h9v11M97 10h13M124 33l7 5h-12"></path>
        </g>
        <circle data-home-ending-wheel cx="18" cy="42" r="5.5"></circle>
        <circle data-home-ending-wheel cx="38" cy="42" r="5.5"></circle>
        <circle data-home-ending-wheel cx="68" cy="42" r="5.5"></circle>
        <circle data-home-ending-wheel cx="110" cy="42" r="5.5"></circle>
        <circle cx="18" cy="42" r="1.3"></circle>
        <circle cx="38" cy="42" r="1.3"></circle>
        <circle cx="68" cy="42" r="1.3"></circle>
        <circle cx="110" cy="42" r="1.3"></circle>
      </svg>
    </div>
  </div>
  <p class="home-ending-caption">{{ T "homeEndingThought" }}</p>
  <a class="home-ending-return" data-home-ending-return href="#home-top">{{ T "homeEndingReturn" }}</a>
</div>
{{- $script := resources.Get "js/home-ending.mjs" | fingerprint "sha256" }}
<script type="module" src="{{ $script.RelPermalink }}" integrity="{{ $script.Data.Integrity }}"></script>
```

The outer lane clips the journey. The runner is the responsive translation surface; the SVG is decorative and contains explicit train parts so its silhouette remains recognizable at small size.

- [ ] **Step 4: Update both catalogs**

Delete the unused `[homeEndingLead]` blocks. Set the remaining message in `i18n/en.toml` to:

```toml
[homeEndingThought]
other = "there goes my train of thought."
```

Set the remaining message in `i18n/zh.toml` to:

```toml
[homeEndingThought]
other = "思绪又飘走了。"
```

Leave both localized `[homeEndingReturn]` values unchanged.

- [ ] **Step 5: Run the focused generated-site test and verify green**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_train_of_thought_is_localized_home_only_and_base_path_safe -v
```

Expected: PASS for English and Chinese under both root and project-subpath builds.

- [ ] **Step 6: Commit the markup and localization slice**

```bash
git add tests/test_site.py layouts/_partials/home-ending.html i18n/en.toml i18n/zh.toml
git commit -m "feat: add train of thought homepage ending"
```

### Task 2: Animate the train before revealing the line

**Files:**
- Modify: `tests/test_site.py:2436-2468`
- Modify: `assets/css/site.css:249-352`

- [ ] **Step 1: Replace the balloon CSS test with a failing train sequence test**

Rename the test to `test_home_ending_has_large_gap_train_sequence_and_reduced_fallback` and use:

```python
def test_home_ending_has_large_gap_train_sequence_and_reduced_fallback(self):
    css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")

    self.assertRegex(
        css,
        r"\.home-ending\s*\{[^}]*"
        r"margin-block-start:\s*clamp\(8rem,\s*25vh,\s*15rem\);",
    )
    for name in (
        "home-ending-train-crossing",
        "home-ending-train-bob",
        "home-ending-caption",
        "home-ending-return",
    ):
        self.assertEqual(1, css.count(f"@keyframes {name}"))
    for removed_name in (
        "home-ending-balloon",
        "home-ending-dot-one",
        "home-ending-dot-two",
        "home-ending-dot-three",
    ):
        self.assertNotIn(removed_name, css)
    self.assertRegex(
        css,
        r"\.home-ending-lane\s*\{[^}]*"
        r"overflow:\s*hidden;[^}]*position:\s*relative;",
    )
    self.assertRegex(
        css,
        r"\.home-ending-train\s*\{[^}]*"
        r"color:\s*var\(--text-color-secondary\);[^}]*"
        r"height:\s*3\.25rem;[^}]*width:\s*8\.25rem;",
    )
    self.assertIn("animation-iteration-count: 1", css)
    self.assertNotIn("animation-iteration-count: infinite", css)
    self.assertRegex(
        css,
        r'\[data-home-ending-state="playing"\] \.home-ending-caption\s*'
        r"\{[^}]*animation-delay:\s*3s;",
    )
    reduced = re.search(
        r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([\s\S]*)\}\s*$",
        css,
    )
    self.assertIsNotNone(reduced)
    self.assertIn("animation: none", reduced.group(1))
    self.assertIn("visibility: visible", reduced.group(1))
```

- [ ] **Step 2: Run the focused CSS test and verify the red state**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_home_ending_has_large_gap_train_sequence_and_reduced_fallback -v
```

Expected: FAIL because `assets/css/site.css` still defines the balloon keyframe and has no train lane, runner, or caption sequence.

- [ ] **Step 3: Replace the balloon CSS block**

Replace the existing `.home-ending` through reduced-motion ending block with:

```css
.home-ending {
  color: var(--text-color-tertiary);
  margin-block-start: clamp(8rem, 25vh, 15rem);
  min-height: 10rem;
  padding-block-end: 2rem;
  text-align: center;
}

.home-ending-lane {
  block-size: 4rem;
  margin-inline: auto;
  max-inline-size: 42rem;
  overflow: hidden;
  position: relative;
}

.home-ending-train-runner {
  align-items: center;
  display: flex;
  inset: 0;
  justify-content: center;
  position: absolute;
}

.home-ending-train {
  color: var(--text-color-secondary);
  flex: none;
  height: 3.25rem;
  overflow: visible;
  width: 8.25rem;
}

.home-ending-caption {
  margin: 0.35rem 0 0;
}

.home-ending-return {
  display: inline-block;
  font-size: 0.8em;
  margin-block-start: 1.25rem;
}

[data-home-ending-enhanced="true"][data-home-ending-state="idle"] .home-ending-train-runner {
  justify-content: flex-end;
  transform: translateX(-100%);
}

[data-home-ending-enhanced="true"][data-home-ending-state="idle"] .home-ending-caption,
[data-home-ending-enhanced="true"][data-home-ending-state="idle"] .home-ending-return {
  opacity: 0;
  pointer-events: none;
  visibility: hidden;
}

[data-home-ending-state="playing"] .home-ending-train-runner,
[data-home-ending-state="playing"] .home-ending-train,
[data-home-ending-state="playing"] .home-ending-caption,
[data-home-ending-state="playing"] .home-ending-return {
  animation-fill-mode: both;
  animation-iteration-count: 1;
}

[data-home-ending-state="playing"] .home-ending-train-runner {
  animation-duration: 3s;
  animation-name: home-ending-train-crossing;
  animation-timing-function: cubic-bezier(0.45, 0.05, 0.3, 1);
  justify-content: flex-end;
}

[data-home-ending-state="playing"] .home-ending-train {
  animation-duration: 3s;
  animation-name: home-ending-train-bob;
  animation-timing-function: linear;
}

[data-home-ending-state="playing"] .home-ending-caption {
  animation-delay: 3s;
  animation-duration: 550ms;
  animation-name: home-ending-caption;
  opacity: 0;
  visibility: hidden;
}

[data-home-ending-state="playing"] .home-ending-return {
  animation-delay: 3.4s;
  animation-duration: 550ms;
  animation-name: home-ending-return;
  opacity: 0;
  visibility: hidden;
}

[data-home-ending-state="complete"] .home-ending-train-runner {
  opacity: 0;
}

[data-home-ending-state="complete"] .home-ending-caption,
[data-home-ending-state="complete"] .home-ending-return,
[data-home-ending-state="reduced"] .home-ending-caption,
[data-home-ending-state="reduced"] .home-ending-return {
  opacity: 1;
  visibility: visible;
}

@keyframes home-ending-train-crossing {
  from {
    transform: translateX(-100%);
  }

  to {
    transform: translateX(50%);
  }
}

@keyframes home-ending-train-bob {
  0%, 100% {
    transform: translateY(0) rotate(0);
  }

  20% {
    transform: translateY(-0.12rem) rotate(0.35deg);
  }

  45% {
    transform: translateY(0.08rem) rotate(-0.25deg);
  }

  70% {
    transform: translateY(-0.08rem) rotate(0.2deg);
  }
}

@keyframes home-ending-caption {
  from {
    opacity: 0;
    transform: translateY(0.25rem);
    visibility: visible;
  }

  to {
    opacity: 1;
    transform: translateY(0);
    visibility: visible;
  }
}

@keyframes home-ending-return {
  from {
    opacity: 0;
    visibility: visible;
  }

  to {
    opacity: 1;
    visibility: visible;
  }
}

@media (prefers-reduced-motion: reduce) {
  .home-ending-train-runner,
  .home-ending-train,
  .home-ending-caption,
  .home-ending-return {
    animation: none !important;
  }

  [data-home-ending] .home-ending-train-runner {
    justify-content: center;
    opacity: 1;
    transform: none;
  }

  [data-home-ending] .home-ending-caption,
  [data-home-ending] .home-ending-return {
    opacity: 1;
    pointer-events: auto;
    visibility: visible;
  }
}
```

The runner starts with its right-aligned train exactly one lane-width to the left and ends a half lane-width beyond the right edge. The caption delay equals the crossing duration, so the phrase does not appear before the train has exited. The nested SVG receives a one-shot bob without introducing any infinite animation.

- [ ] **Step 4: Run the focused CSS test and verify green**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_home_ending_has_large_gap_train_sequence_and_reduced_fallback -v
```

Expected: PASS.

- [ ] **Step 5: Run the generated-site test with the new styles**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_train_of_thought_is_localized_home_only_and_base_path_safe -v
```

Expected: PASS.

- [ ] **Step 6: Commit the animation slice**

```bash
git add tests/test_site.py assets/css/site.css
git commit -m "style: send the train of thought away"
```

### Task 3: Preserve and name the replay behavior

**Files:**
- Modify: `tests/home-ending.test.mjs:48`
- Verify: `assets/js/home-ending.mjs`

- [ ] **Step 1: Rename the behavioral test**

Change only the first test title:

```javascript
test("return link re-arms the train only after a full viewport exit", () => {
```

No production JavaScript change is required: the module targets only the ending root and return link, and its `idle` → `playing` → `complete` state contract is independent of the decorative SVG.

- [ ] **Step 2: Run the dedicated Node test**

Run:

```bash
node --test tests/home-ending.test.mjs
```

Expected: 3 tests pass, including replay after full viewport exit, reduced-motion scrolling, and missing-IntersectionObserver fallback.

- [ ] **Step 3: Commit the terminology cleanup**

```bash
git add tests/home-ending.test.mjs
git commit -m "test: describe train replay behavior"
```

### Task 4: Verify and render the second prototype

**Files:**
- Verify: all changed files

- [ ] **Step 1: Check syntax and stale prototype terms**

Run:

```bash
git diff --check HEAD~3..HEAD
node --check assets/js/home-ending.mjs
rg -n "homeEndingLead|home-ending-balloon|home-ending-dot|There was one more thing|好像还有件事" layouts assets i18n
```

Expected: the first two commands exit 0; `rg` exits 1 with no stale implementation references.

- [ ] **Step 2: Run the complete automated suite**

Run:

```bash
python3 scripts/validate_interaction_ids.py content
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
actionlint .github/workflows/hugo.yml
```

Expected: interaction IDs validate, all Python and Node tests pass, and the workflow linter reports no errors.

- [ ] **Step 3: Run strict root and project-subpath builds**

Run:

```bash
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir --printI18nWarnings --printPathWarnings --baseURL https://example.org/
python3 scripts/check_site.py public --base-url https://example.org/
```

Then create a temporary destination with `mktemp -d` and run the same strict Hugo build with `--baseURL https://example.github.io/example-blog/`, followed by `scripts/check_site.py` using the matching base URL.

Expected: both Hugo builds and both site checks exit 0 without warnings.

- [ ] **Step 4: Inspect the rendered homepage contract**

Against the existing local Hugo preview, inspect `/` and `/zh/` at desktop and narrow widths. Confirm that the train begins offscreen, crosses without horizontal page overflow, fully exits before the line appears, the localized line is correct, the return link scrolls to the top, and scrolling back to the bottom replays only after the ending has left the viewport.

- [ ] **Step 5: Leave the preview running for user review**

Report the local English and Chinese homepage URLs. Do not merge or delete the worktree while the user is comparing the prototype.
