# Filled Train and Hard Restart Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rejected thin train with a larger filled toy steam train that crosses in 5.5 seconds, and make the blue start-over link perform a guaranteed page reload at `#home-top`.

**Architecture:** Keep the homepage partial, localized caption, CSS state attributes, and one-shot IntersectionObserver trigger. Simplify the ES module by removing scroll-and-rearm state: the observer disconnects after the first activation, while the link sets the top fragment and reloads the current document. Replace the SVG and its CSS as a separate visual slice so replay behavior and appearance each have an isolated red-green cycle.

**Tech Stack:** Hugo templates, inline SVG, CSS keyframes, dependency-free ES modules, Python `unittest`, Node's built-in test runner.

---

## File Structure

- Modify `tests/home-ending.test.mjs`: specify fragment-plus-reload behavior and one-shot observer cleanup.
- Modify `assets/js/home-ending.mjs`: replace scroll/rearm logic with an injected location object and literal reload.
- Modify `tests/test_site.py`: specify the filled toy-train SVG structure, size, animation duration, delayed caption, rotating wheels, smoke, and reduced-motion fallback.
- Modify `layouts/_partials/home-ending.html`: replace the thin outlined SVG with rounded filled geometry and page-background cut-outs.
- Modify `assets/css/site.css`: style the filled train and run a 5.5-second one-shot crossing with wheel and smoke motion.

### Task 1: Make start over perform a literal restart

**Files:**
- Modify: `tests/home-ending.test.mjs:48-119`
- Modify: `assets/js/home-ending.mjs:1-69`

- [ ] **Step 1: Replace the replay test with a failing hard-reload test**

Replace the first Node test with:

```javascript
test("return link reloads the homepage at the top after one train journey", () => {
  const { link, root } = endingDom();
  const { FakeIntersectionObserver, instances } = observerHarness();
  const location = {
    hash: "",
    reloadCalls: 0,
    reload() {
      this.reloadCalls += 1;
    },
  };
  mountHomeEnding(root, {
    IntersectionObserverImpl: FakeIntersectionObserver,
    locationImpl: location,
    matchMediaImpl: () => ({ matches: false }),
  });

  assert.equal(root.dataset.homeEndingEnhanced, "true");
  assert.equal(root.dataset.homeEndingState, "idle");
  assert.deepEqual(instances[0].observed, [root]);
  instances[0].trigger(false);
  assert.equal(root.dataset.homeEndingState, "idle");
  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "playing");
  assert.equal(instances[0].disconnected, true);

  link.dispatch("animationend");
  assert.equal(root.dataset.homeEndingState, "complete");
  let prevented = false;
  link.dispatch("click", { preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(location.hash, "#home-top");
  assert.equal(location.reloadCalls, 1);
});
```

Replace the reduced-motion test with:

```javascript
test("reduced motion stays static and hard-reloads at the top", () => {
  const { link, root } = endingDom();
  const { FakeIntersectionObserver, instances } = observerHarness();
  const location = {
    hash: "",
    reloadCalls: 0,
    reload() {
      this.reloadCalls += 1;
    },
  };
  mountHomeEnding(root, {
    IntersectionObserverImpl: FakeIntersectionObserver,
    locationImpl: location,
    matchMediaImpl: () => ({ matches: true }),
  });

  assert.equal(root.dataset.homeEndingState, "reduced");
  assert.equal(instances.length, 0);
  let prevented = false;
  link.dispatch("click", { preventDefault: () => { prevented = true; } });
assert.equal(prevented, true);
assert.equal(location.hash, "#home-top");
assert.equal(location.reloadCalls, 1);
});
```

- [ ] **Step 2: Run the Node test and verify the red state**

Run:

```bash
node --test tests/home-ending.test.mjs
```

Expected: FAIL because the current handler ignores `locationImpl`, does not set `#home-top`, does not reload, and leaves the observer connected for re-arming.

- [ ] **Step 3: Simplify the module to one-shot activation plus reload**

Replace `mountHomeEnding` with:

```javascript
export function mountHomeEnding(root, options = {}) {
  const IntersectionObserverImpl = Object.hasOwn(options, "IntersectionObserverImpl")
    ? options.IntersectionObserverImpl
    : globalThis.IntersectionObserver;
  const matchMediaImpl = Object.hasOwn(options, "matchMediaImpl")
    ? options.matchMediaImpl
    : (typeof globalThis.matchMedia === "function"
      ? globalThis.matchMedia.bind(globalThis)
      : undefined);
  const locationImpl = Object.hasOwn(options, "locationImpl")
    ? options.locationImpl
    : globalThis.location;
  const reducedMotion = Boolean(
    matchMediaImpl?.("(prefers-reduced-motion: reduce)")?.matches,
  );
  const returnLink = root.querySelector("[data-home-ending-return]");
  let observer = null;

  root.dataset.homeEndingEnhanced = "true";
  returnLink?.addEventListener("animationend", () => {
    if (root.dataset.homeEndingState === "playing") {
      root.dataset.homeEndingState = "complete";
    }
  });
  returnLink?.addEventListener("click", (event) => {
    if (typeof locationImpl?.reload !== "function") return;
    event.preventDefault();
    locationImpl.hash = "#home-top";
    locationImpl.reload();
  });

  if (reducedMotion) {
    root.dataset.homeEndingState = "reduced";
    return { observer: null };
  }
  if (typeof IntersectionObserverImpl !== "function") {
    root.dataset.homeEndingState = "complete";
    return { observer: null };
  }

  root.dataset.homeEndingState = "idle";
  observer = new IntersectionObserverImpl((entries) => {
    if (!entries.some((entry) => entry.isIntersecting)) return;
    root.dataset.homeEndingState = "playing";
    observer.disconnect();
  });
  observer.observe(root);
  return { observer };
}
```

Leave `mountAll` and the DOM-ready mounting block below the function unchanged.

- [ ] **Step 4: Run the dedicated Node suite and syntax check**

Run:

```bash
node --test tests/home-ending.test.mjs
node --check assets/js/home-ending.mjs
```

Expected: all 3 tests pass and the syntax check exits 0.

- [ ] **Step 5: Commit the restart fix**

```bash
git add assets/js/home-ending.mjs tests/home-ending.test.mjs
git commit -m "fix: hard-restart the homepage ending"
```

### Task 2: Replace the thin SVG with a filled toy train

**Files:**
- Modify: `tests/test_site.py:1891-2013`
- Modify: `layouts/_partials/home-ending.html:1-31`

- [ ] **Step 1: Change the generated-markup assertions first**

In `test_train_of_thought_is_localized_home_only_and_base_path_safe`, change the SVG dimensions to `viewBox="0 0 168 64"`, `width="168"`, and `height="64"`. Replace the train-part assertions with:

```python
self.assertEqual(1, ending.count("data-home-ending-carriage"))
self.assertEqual(1, ending.count("data-home-ending-engine"))
self.assertEqual(3, ending.count("data-home-ending-smoke"))
self.assertEqual(4, ending.count("data-home-ending-wheel"))
self.assertEqual(8, ending.count("data-home-ending-cutout"))
self.assertIn('fill="currentColor"', ending)
self.assertIn('stroke="none"', ending)
```

Keep the localization, home-only, ordering, media exclusion, module integrity, and base-path assertions unchanged.

- [ ] **Step 2: Run the generated-site test and verify the red state**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_train_of_thought_is_localized_home_only_and_base_path_safe -v
```

Expected: FAIL because the existing SVG is `132 × 52`, outlined, has two smoke circles, and has no filled cut-outs.

- [ ] **Step 3: Replace only the SVG inside the existing lane**

Keep the ending root, lane, runner, caption, return link, and module include. Replace the SVG with:

```html
<svg class="home-ending-train" data-home-ending-train viewBox="0 0 168 64" width="168" height="64" fill="currentColor" stroke="none" aria-hidden="true" focusable="false">
  <g class="home-ending-smoke-cloud">
    <circle class="home-ending-smoke" data-home-ending-smoke cx="129" cy="6" r="5"></circle>
    <circle class="home-ending-smoke" data-home-ending-smoke cx="116" cy="5" r="3.5"></circle>
    <circle class="home-ending-smoke" data-home-ending-smoke cx="106" cy="10" r="2.5"></circle>
  </g>
  <g data-home-ending-carriage>
    <rect x="4" y="28" width="54" height="22" rx="6"></rect>
    <rect x="9" y="21" width="44" height="10" rx="5"></rect>
    <rect class="home-ending-train-cutout" data-home-ending-cutout x="13" y="32" width="14" height="10" rx="3"></rect>
    <rect class="home-ending-train-cutout" data-home-ending-cutout x="33" y="32" width="14" height="10" rx="3"></rect>
  </g>
  <rect x="57" y="41" width="10" height="4" rx="2"></rect>
  <g data-home-ending-engine>
    <rect x="65" y="18" width="34" height="32" rx="5"></rect>
    <rect x="61" y="13" width="42" height="8" rx="4"></rect>
    <rect class="home-ending-train-cutout" data-home-ending-cutout x="72" y="24" width="19" height="12" rx="3"></rect>
    <rect x="93" y="29" width="56" height="21" rx="10.5"></rect>
    <rect x="120" y="12" width="12" height="19" rx="3"></rect>
    <rect x="117" y="9" width="18" height="6" rx="3"></rect>
    <circle class="home-ending-train-cutout" data-home-ending-cutout cx="145" cy="34" r="3"></circle>
    <path d="M148 41h8l9 10h-17Z"></path>
  </g>
  <g class="home-ending-wheel" data-home-ending-wheel>
    <circle cx="18" cy="52" r="8"></circle>
    <path class="home-ending-wheel-cut" d="M13 52h10M18 47v10"></path>
    <circle class="home-ending-train-cutout" data-home-ending-cutout cx="18" cy="52" r="2.25"></circle>
  </g>
  <g class="home-ending-wheel" data-home-ending-wheel>
    <circle cx="45" cy="52" r="8"></circle>
    <path class="home-ending-wheel-cut" d="M40 52h10M45 47v10"></path>
    <circle class="home-ending-train-cutout" data-home-ending-cutout cx="45" cy="52" r="2.25"></circle>
  </g>
  <g class="home-ending-wheel" data-home-ending-wheel>
    <circle cx="80" cy="52" r="9"></circle>
    <path class="home-ending-wheel-cut" d="M74 52h12M80 46v12"></path>
    <circle class="home-ending-train-cutout" data-home-ending-cutout cx="80" cy="52" r="2.5"></circle>
  </g>
  <g class="home-ending-wheel" data-home-ending-wheel>
    <circle cx="135" cy="52" r="9"></circle>
    <path class="home-ending-wheel-cut" d="M129 52h12M135 46v12"></path>
    <circle class="home-ending-train-cutout" data-home-ending-cutout cx="135" cy="52" r="2.5"></circle>
  </g>
</svg>
```

The filled bodies create a clear toy silhouette. Eight background-colored cut-outs provide three windows, one lamp, and four wheel hubs without reintroducing the rejected outline clutter.

- [ ] **Step 4: Run the generated-site test and verify green**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_train_of_thought_is_localized_home_only_and_base_path_safe -v
```

Expected: PASS for English and Chinese under both base URL modes.

- [ ] **Step 5: Commit the new train geometry**

```bash
git add layouts/_partials/home-ending.html tests/test_site.py
git commit -m "feat: redraw the train as a filled toy"
```

### Task 3: Slow the journey and animate wheels and smoke

**Files:**
- Modify: `tests/test_site.py:2447-2495`
- Modify: `assets/css/site.css:249-427`

- [ ] **Step 1: Tighten the CSS contract before changing styles**

In `test_home_ending_has_large_gap_train_sequence_and_reduced_fallback`, require these keyframes exactly once:

```python
for name in (
    "home-ending-train-crossing",
    "home-ending-train-bob",
    "home-ending-wheel-turn",
    "home-ending-smoke-drift",
    "home-ending-caption",
    "home-ending-return",
):
    self.assertEqual(1, css.count(f"@keyframes {name}"))
```

Change the train-size assertion to `height: 4rem` and `width: 10.5rem`. Add:

```python
self.assertRegex(
    css,
    r'\[data-home-ending-state="playing"\] \.home-ending-train-runner\s*'
    r"\{[^}]*animation-duration:\s*5\.5s;",
)
self.assertRegex(
    css,
    r'\[data-home-ending-state="playing"\] \.home-ending-caption\s*'
    r"\{[^}]*animation-delay:\s*5\.5s;",
)
self.assertRegex(
    css,
    r"\.home-ending-train-cutout\s*\{[^}]*"
    r"fill:\s*var\(--bg-color-primary\);",
)
self.assertRegex(
    css,
    r"\.home-ending-wheel\s*\{[^}]*transform-box:\s*fill-box;",
)
self.assertNotIn("animation-iteration-count: infinite", css)
```

Keep the large-gap, clipped-lane, one-shot, removed-balloon, and reduced-motion assertions.

- [ ] **Step 2: Run the CSS test and verify the red state**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_home_ending_has_large_gap_train_sequence_and_reduced_fallback -v
```

Expected: FAIL because the stylesheet still uses a 3-second `8.25rem × 3.25rem` outline train and defines no wheel or smoke keyframes.

- [ ] **Step 3: Update the train's base visual styles**

Change `.home-ending-lane` to `block-size: 4.75rem`. Replace the train rule and add the cut-out rules:

```css
.home-ending-train {
  color: var(--text-color-secondary);
  flex: none;
  height: 4rem;
  overflow: visible;
  width: 10.5rem;
}

.home-ending-train-cutout {
  fill: var(--bg-color-primary);
}

.home-ending-wheel-cut {
  fill: none;
  stroke: var(--bg-color-primary);
  stroke-linecap: round;
  stroke-width: 2;
}

.home-ending-wheel {
  transform-box: fill-box;
  transform-origin: center;
}

.home-ending-smoke-cloud {
  opacity: 0.45;
  transform-box: fill-box;
  transform-origin: center;
}
```

- [ ] **Step 4: Update the playing sequence and delays**

Replace the playing-state one-shot animation group with:

```css
[data-home-ending-state="playing"] .home-ending-train-runner,
[data-home-ending-state="playing"] .home-ending-train,
[data-home-ending-state="playing"] .home-ending-wheel,
[data-home-ending-state="playing"] .home-ending-smoke-cloud,
[data-home-ending-state="playing"] .home-ending-caption,
[data-home-ending-state="playing"] .home-ending-return {
  animation-fill-mode: both;
  animation-iteration-count: 1;
}
```

Then use:

```css
[data-home-ending-state="playing"] .home-ending-train-runner {
  animation-duration: 5.5s;
  animation-name: home-ending-train-crossing;
  animation-timing-function: linear;
  justify-content: flex-end;
}

[data-home-ending-state="playing"] .home-ending-train {
  animation-duration: 5.5s;
  animation-name: home-ending-train-bob;
  animation-timing-function: linear;
}

[data-home-ending-state="playing"] .home-ending-wheel {
  animation-duration: 5.5s;
  animation-name: home-ending-wheel-turn;
  animation-timing-function: linear;
}

[data-home-ending-state="playing"] .home-ending-smoke-cloud {
  animation-duration: 5.5s;
  animation-name: home-ending-smoke-drift;
  animation-timing-function: ease-out;
}

[data-home-ending-state="playing"] .home-ending-caption {
  animation-delay: 5.5s;
  animation-duration: 550ms;
  animation-name: home-ending-caption;
  opacity: 0;
  visibility: hidden;
}

[data-home-ending-state="playing"] .home-ending-return {
  animation-delay: 5.9s;
  animation-duration: 550ms;
  animation-name: home-ending-return;
  opacity: 0;
  visibility: hidden;
}
```

Keep the runner's `translateX(-100%)` to `translateX(50%)` crossing so the larger train begins and ends outside the clipped lane.

- [ ] **Step 5: Add one-shot wheel and smoke keyframes**

Add:

```css
@keyframes home-ending-wheel-turn {
  to {
    transform: rotate(1080deg);
  }
}

@keyframes home-ending-smoke-drift {
  from {
    opacity: 0.2;
    transform: translate(0, 0.15rem) scale(0.9);
  }

  35% {
    opacity: 0.5;
  }

  to {
    opacity: 0;
    transform: translate(-0.8rem, -0.65rem) scale(1.2);
  }
}
```

Retain the existing gentle one-shot bob, caption fade, and return-link fade. Add `.home-ending-wheel` and `.home-ending-smoke-cloud` to the reduced-motion `animation: none !important` selector so the static composition has no wheel or smoke movement.

- [ ] **Step 6: Run both focused site tests and verify green**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_train_of_thought_is_localized_home_only_and_base_path_safe \
  tests.test_site.GeneratedSiteTests.test_home_ending_has_large_gap_train_sequence_and_reduced_fallback \
  -v
```

Expected: both tests pass.

- [ ] **Step 7: Commit the slower animation**

```bash
git add assets/css/site.css tests/test_site.py
git commit -m "style: slow and soften the toy train"
```

### Task 4: Verify and refresh the review build

**Files:**
- Verify: all changed production, test, and documentation files

- [ ] **Step 1: Check syntax, formatting, and stale replay code**

Run:

```bash
git diff --check HEAD~3..HEAD
node --check assets/js/home-ending.mjs
rg -n "scrollToImpl|waitingForExit|armed|home-ending-balloon|home-ending-dot" assets layouts i18n
```

Expected: the first two commands exit 0; `rg` exits 1 because the old replay and rejected visual identifiers are absent from production files.

- [ ] **Step 2: Run the full verification suite**

Run:

```bash
python3 scripts/validate_interaction_ids.py content
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
actionlint .github/workflows/hugo.yml
```

Expected: interaction IDs validate, all Python and Node tests pass, and `actionlint` reports no errors.

- [ ] **Step 3: Run strict root and project-subpath builds**

Run:

```bash
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.org/
python3 scripts/check_site.py public --base-url https://example.org/

TRAIN_REVIEW_BUILD="$(mktemp -d /tmp/blog-filled-train.XXXXXX)"
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.github.io/example-blog/ \
  --destination "$TRAIN_REVIEW_BUILD"
python3 scripts/check_site.py "$TRAIN_REVIEW_BUILD" \
  --base-url https://example.github.io/example-blog/
```

Expected: both Hugo builds and both base-path checks exit 0 without warnings.

- [ ] **Step 4: Confirm the live review responses**

Against the existing watcher on port 1314, verify `/` contains `there goes my train of thought.`, `/zh/` contains `思绪又飘走了。`, and both contain the `168 × 64` filled train plus the newly fingerprinted homepage-ending module.

- [ ] **Step 5: Leave the branch and watcher intact**

Keep `feature/escaping-thought` and `/Users/allan/GitHub/blog/.worktrees/escaping-thought` for the user's next visual review. Do not merge or remove the worktree.
