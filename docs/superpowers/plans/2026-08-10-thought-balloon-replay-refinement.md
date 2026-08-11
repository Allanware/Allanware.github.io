# Thought Balloon Replay Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the escaping ellipsis with a clear outlined thought balloon and make the return link re-arm the animation for the reader's next visit to the bottom.

**Architecture:** The existing homepage-ending partial keeps its localized text and replaces only the decorative dot spans with one inline SVG. The existing ES module keeps a persistent `IntersectionObserver` with explicit armed/waiting-for-exit state, so clicking the return link scrolls upward without replaying until the ending has fully left and re-entered the viewport. CSS replaces the three dot keyframes and the rejected staged dot-enlargement rule with one balloon animation.

**Tech Stack:** Hugo templates, inline SVG, CSS animations, browser `IntersectionObserver`/`matchMedia`/`scrollTo`, Python `unittest`, Node's built-in test runner.

**Scope:** This plan refines only prototype 1. It does not implement the train prototype, change localized copy, or alter homepage spacing, Popular posts, the global footer, or non-home pages.

---

## File Structure

- Modify `layouts/_partials/home-ending.html`: replace three decorative periods with the accessible-hidden outlined SVG thought balloon.
- Modify `assets/js/home-ending.mjs`: keep one observer alive, re-arm after link activation and full viewport exit, and replay on the next entry.
- Modify `assets/css/site.css`: remove dot sizing/keyframes and style/animate the thought balloon.
- Modify `tests/test_site.py`: update generated markup and CSS contracts from dots to the SVG balloon.
- Modify `tests/home-ending.test.mjs`: prove exit-gated replay and preserve reduced-motion/fallback behavior.

### Task 0: Remove the rejected uncommitted dot-enlargement experiment

**Files:**
- Modify: `assets/css/site.css`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Delete the staged dot-enlargement rule**

Remove this exact block from `assets/css/site.css`:

```css
[data-home-ending-dot] {
  color: var(--text-color-secondary);
  font-size: 1.5em;
  font-weight: 700;
  line-height: 0;
  margin-inline: 0.025em;
}
```

- [ ] **Step 2: Delete its staged CSS assertion**

Remove this exact block from
`test_home_ending_has_large_gap_one_shot_motion_and_reduced_fallback` in
`tests/test_site.py`:

```python
        self.assertRegex(
            css,
            r"\[data-home-ending-dot\]\s*\{[^}]*"
            r"color:\s*var\(--text-color-secondary\);[^}]*"
            r"font-size:\s*1\.5em;[^}]*"
            r"font-weight:\s*700;",
        )
```

- [ ] **Step 3: Synchronize the index with the restored files**

Run:

```bash
git add assets/css/site.css tests/test_site.py
git diff --cached --check
git status --short
```

Expected: neither file appears in `git status --short`; no rejected-dot change
remains staged or unstaged. Do not create a commit because this task only
removes an uncommitted experiment.

### Task 1: Thought-balloon markup

**Files:**
- Modify: `tests/test_site.py`
- Modify: `layouts/_partials/home-ending.html`

- [ ] **Step 1: Update the generated-site test to require a thought balloon**

In `test_escaping_thought_is_localized_home_only_and_base_path_safe`, replace the dot-count assertion with:

```python
                        ending = html[
                            html.index('<div class="home-ending"'):
                            html.index("<footer>")
                        ]
                        self.assertEqual(1, ending.count("data-home-ending-balloon"))
                        self.assertNotIn("data-home-ending-dot", ending)
                        self.assertRegex(
                            ending,
                            r'<svg\b(?=[^>]*\bdata-home-ending-balloon(?:\s|>))'
                            r'(?=[^>]*\bviewBox="0 0 64 48")'
                            r'(?=[^>]*\bwidth="36")'
                            r'(?=[^>]*\bheight="27")'
                            r'(?=[^>]*\baria-hidden="true")'
                            r'(?=[^>]*\bfocusable="false")[^>]*>',
                        )
                        self.assertEqual(1, ending.count("<path "))
                        self.assertEqual(2, ending.count("<circle "))
```

Keep the existing assertion that the ending contains no `img`, `picture`, or `video` element; inline SVG is the intentional code-native visual.

- [ ] **Step 2: Run the generated-site test and verify it fails on the dot markup**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_escaping_thought_is_localized_home_only_and_base_path_safe -v
```

Expected: `FAIL` because the ending has no `data-home-ending-balloon` SVG and still contains `data-home-ending-dot`.

- [ ] **Step 3: Replace the decorative dots with the outlined thought balloon**

Replace the paragraph inside `layouts/_partials/home-ending.html` with:

```go-html-template
  <p class="home-ending-thought" aria-label="{{ T "homeEndingThought" }}">
    <span aria-hidden="true">{{ T "homeEndingLead" }}<svg class="home-ending-balloon" data-home-ending-balloon viewBox="0 0 64 48" width="36" height="27" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
      <path d="M20 34C12.8 34 7 29.3 7 23.5c0-5.1 4.4-9.4 10.3-10.3C19.6 7.8 25.6 5 31 7.8 35.4 2.8 44 3.8 47 10c6.1.4 11 5.1 11 10.9C58 28.1 51.7 34 44 34H20Z"></path>
      <circle cx="15" cy="40" r="3.2"></circle>
      <circle cx="8.5" cy="46" r="1.8"></circle>
    </svg></span>
  </p>
```

The paragraph's existing `aria-label` remains the complete localized thought. Both the wrapper and SVG stay hidden from assistive technology, and the SVG remains non-focusable.

- [ ] **Step 4: Run the generated-site test and verify it passes**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_escaping_thought_is_localized_home_only_and_base_path_safe -v
```

Expected: `OK` with one test passing.

- [ ] **Step 5: Commit the semantic replacement**

```bash
git add layouts/_partials/home-ending.html tests/test_site.py
git commit -m "feat: replace escaping dots with thought balloon"
```

### Task 2: Exit-gated replay

**Files:**
- Modify: `tests/home-ending.test.mjs`
- Modify: `assets/js/home-ending.mjs`

- [ ] **Step 1: Update the viewport test to require replay after exit**

Replace the first test in `tests/home-ending.test.mjs` with:

```javascript
test("return link re-arms the thought only after a full viewport exit", () => {
  const { link, root } = endingDom();
  const { FakeIntersectionObserver, instances } = observerHarness();
  const scrollCalls = [];
  mountHomeEnding(root, {
    IntersectionObserverImpl: FakeIntersectionObserver,
    matchMediaImpl: () => ({ matches: false }),
    scrollToImpl: (options) => scrollCalls.push(options),
  });

  assert.equal(root.dataset.homeEndingEnhanced, "true");
  assert.equal(root.dataset.homeEndingState, "idle");
  assert.deepEqual(instances[0].observed, [root]);
  instances[0].trigger(false);
  assert.equal(root.dataset.homeEndingState, "idle");
  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "playing");
  assert.equal(instances[0].disconnected, false);
  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "playing");

  link.dispatch("animationend");
  assert.equal(root.dataset.homeEndingState, "complete");
  let prevented = false;
  link.dispatch("click", { preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  assert.deepEqual(scrollCalls, [{ top: 0, behavior: "smooth" }]);
  assert.equal(root.dataset.homeEndingState, "complete");

  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "complete");
  instances[0].trigger(false);
  assert.equal(root.dataset.homeEndingState, "idle");
  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "playing");
});
```

- [ ] **Step 2: Run the interaction test and verify the disconnected observer fails**

Run:

```bash
node --test tests/home-ending.test.mjs
```

Expected: `FAIL` because the current observer disconnects after the first entry and the state never returns to `idle` after a later exit.

- [ ] **Step 3: Implement the persistent armed observer**

Replace `mountHomeEnding` in `assets/js/home-ending.mjs` with:

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
  const scrollToImpl = Object.hasOwn(options, "scrollToImpl")
    ? options.scrollToImpl
    : (typeof globalThis.scrollTo === "function"
      ? globalThis.scrollTo.bind(globalThis)
      : undefined);
  const reducedMotion = Boolean(
    matchMediaImpl?.("(prefers-reduced-motion: reduce)")?.matches,
  );
  const returnLink = root.querySelector("[data-home-ending-return]");
  let observer = null;
  let armed = true;
  let waitingForExit = false;

  root.dataset.homeEndingEnhanced = "true";
  returnLink?.addEventListener("animationend", () => {
    if (root.dataset.homeEndingState === "playing") {
      root.dataset.homeEndingState = "complete";
    }
  });
  returnLink?.addEventListener("click", (event) => {
    if (observer) {
      armed = false;
      waitingForExit = true;
    }
    if (typeof scrollToImpl === "function") {
      event.preventDefault();
      scrollToImpl({
        top: 0,
        behavior: reducedMotion ? "auto" : "smooth",
      });
    }
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
    const isIntersecting = entries.some((entry) => entry.isIntersecting);
    if (!isIntersecting) {
      if (waitingForExit) {
        waitingForExit = false;
        armed = true;
        root.dataset.homeEndingState = "idle";
      }
      return;
    }
    if (!armed) return;
    armed = false;
    root.dataset.homeEndingState = "playing";
  });
  observer.observe(root);
  return { observer };
}
```

Keep the existing `mountAll` and DOM-ready auto-mount code unchanged.

- [ ] **Step 4: Run all interaction tests and syntax validation**

Run:

```bash
node --test tests/home-ending.test.mjs
node --check assets/js/home-ending.mjs
```

Expected: all three interaction tests pass and syntax validation exits 0.

- [ ] **Step 5: Commit the replay behavior**

```bash
git add assets/js/home-ending.mjs tests/home-ending.test.mjs
git commit -m "fix: replay escaping thought after starting over"
```

### Task 3: Thought-balloon motion and rejected-dot cleanup

**Files:**
- Modify: `tests/test_site.py`
- Modify: `assets/css/site.css`

- [ ] **Step 1: Replace the dot CSS contract with the balloon contract**

Rename the CSS test to `test_home_ending_has_large_gap_thought_balloon_and_reduced_fallback`. Replace the dot-specific assertions with:

```python
        for name in ("home-ending-balloon", "home-ending-return"):
            self.assertEqual(1, css.count(f"@keyframes {name}"))
        for removed_name in (
            "home-ending-dot-one",
            "home-ending-dot-two",
            "home-ending-dot-three",
        ):
            self.assertNotIn(removed_name, css)
        self.assertRegex(
            css,
            r"\.home-ending-balloon\s*\{[^}]*"
            r"color:\s*var\(--text-color-secondary\);[^}]*"
            r"height:\s*1\.7em;[^}]*"
            r"width:\s*2\.25em;",
        )
        self.assertIn("animation-iteration-count: 1", css)
```

Keep the existing large-gap and reduced-motion assertions.

- [ ] **Step 2: Run the CSS contract and verify it fails on dot keyframes**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_home_ending_has_large_gap_thought_balloon_and_reduced_fallback -v
```

Expected: `FAIL` because the stylesheet still has three dot keyframes and no `home-ending-balloon` keyframe.

- [ ] **Step 3: Replace all dot-specific styling with the balloon styling**

Remove every rule whose selector contains `.home-ending-dots` or
`[data-home-ending-dot]`, including the staged 1.5em dot-enlargement rule.
Remove the `home-ending-dot-one`, `home-ending-dot-two`, and
`home-ending-dot-three` keyframes in full. These exact names are obsolete after
Task 1 replaces the markup, so none may remain in the stylesheet.

Add the balloon's base treatment after `.home-ending-thought`:

```css
.home-ending-thought > [aria-hidden="true"] {
  align-items: center;
  display: inline-flex;
}

.home-ending-balloon {
  color: var(--text-color-secondary);
  flex: none;
  height: 1.7em;
  margin-inline-start: 0.35em;
  overflow: visible;
  width: 2.25em;
}
```

Replace the shared playing selector and balloon states with:

```css
[data-home-ending-state="playing"] .home-ending-balloon,
[data-home-ending-state="playing"] .home-ending-return {
  animation-fill-mode: forwards;
  animation-iteration-count: 1;
}

[data-home-ending-state="playing"] .home-ending-balloon {
  animation-duration: 1.4s;
  animation-name: home-ending-balloon;
  animation-timing-function: cubic-bezier(0.22, 0.7, 0.28, 1);
  transform-origin: center;
}

[data-home-ending-state="playing"] .home-ending-return {
  animation-delay: 1.3s;
  animation-duration: 600ms;
  animation-name: home-ending-return;
  opacity: 0;
  visibility: hidden;
}

[data-home-ending-state="complete"] .home-ending-balloon {
  opacity: 0;
}
```

Replace all dot keyframes with:

```css
@keyframes home-ending-balloon {
  45% {
    opacity: 1;
    transform: translate(1.5rem, -0.75rem) scale(1.06);
  }

  to {
    opacity: 0;
    transform: translate(4.5rem, -2.75rem) scale(0.9);
  }
}
```

Change the reduced-motion selector from `[data-home-ending-dot]` to `.home-ending-balloon`:

```css
@media (prefers-reduced-motion: reduce) {
  .home-ending-balloon,
  .home-ending-return {
    animation: none !important;
  }

  [data-home-ending] .home-ending-return {
    opacity: 1;
    pointer-events: auto;
    visibility: visible;
  }
}
```

- [ ] **Step 4: Run focused markup, CSS, and interaction tests**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_escaping_thought_is_localized_home_only_and_base_path_safe \
  tests.test_site.GeneratedSiteTests.test_home_ending_has_large_gap_thought_balloon_and_reduced_fallback \
  -v
node --test tests/home-ending.test.mjs
```

Expected: two Python methods and three Node cases pass.

- [ ] **Step 5: Commit the visual replacement**

```bash
git add assets/css/site.css tests/test_site.py
git commit -m "style: float the thought balloon away"
```

### Task 4: Full verification and refreshed preview

**Files:**
- Verify only; no expected source changes.

- [ ] **Step 1: Run all automated tests and validators**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
node --check assets/js/home-ending.mjs
python3 scripts/validate_interaction_ids.py content
```

Expected: every Python and Node test passes, JavaScript syntax validation exits 0, and interaction ID validation passes. The Node suite requires loopback permission for its existing Kudos HTTP-server test.

- [ ] **Step 2: Run strict root and project-subpath builds**

Create a dedicated temporary directory with `mktemp -d`, then run both
build/check pairs in the same shell using its explicit writable cache directory:

```bash
ENDING_VERIFY_DIR="$(mktemp -d /tmp/thought-balloon.XXXXXX)"
hugo --cleanDestinationDir --panicOnWarning --noBuildLock --gc --environment production --cacheDir "$ENDING_VERIFY_DIR/cache" --destination "$ENDING_VERIFY_DIR/root" --baseURL https://example.test/
python3 scripts/check_site.py "$ENDING_VERIFY_DIR/root" --base-url https://example.test/
hugo --cleanDestinationDir --panicOnWarning --noBuildLock --gc --environment production --cacheDir "$ENDING_VERIFY_DIR/cache" --destination "$ENDING_VERIFY_DIR/project" --baseURL https://example.test/example-blog/
python3 scripts/check_site.py "$ENDING_VERIFY_DIR/project" --base-url https://example.test/example-blog/
```

Expected: both Hugo builds complete without warnings and both base-path checks pass.

- [ ] **Step 3: Confirm the live review server rebuilt**

The existing isolated-worktree server runs at `http://localhost:1314/`. Confirm its log reports an asset/template rebuild and verify both URLs return the thought-balloon marker:

```bash
curl -fsS http://127.0.0.1:1314/
curl -fsS http://127.0.0.1:1314/zh/
```

Expected: both responses contain `data-home-ending-balloon` and neither contains `data-home-ending-dot`.

- [ ] **Step 4: Hand off the revised prototype for visual review**

Ask the user to reload the English or Chinese homepage, scroll to the bottom, click the return link, wait until the ending has left the viewport, then scroll back down and confirm the balloon replays without refreshing.
