# Escaping Thought Homepage Ending Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first, escaping-thought prototype to the bottom of only the English and Chinese homepages and serve it locally for visual review.

**Architecture:** A homepage-only Hugo partial owns the localized, progressively enhanced markup and fingerprints its dedicated ES module. The module changes a small state machine (`static` → `idle` → `playing` → `complete`, with `reduced` and no-observer fallbacks), while site-local CSS owns all movement and presentation. Existing generated-site tests cover placement and asset delivery; a focused dependency-free Node suite covers the interaction state machine.

**Tech Stack:** Hugo templates and Pipes, TOML i18n catalogs, CSS animations, browser `IntersectionObserver`/`matchMedia`/`scrollTo`, Python `unittest`, Node's built-in test runner.

**Scope:** This plan ends at the first in-site review checkpoint. The train-of-thought version receives its own replacement plan after the escaping-thought prototype has been reviewed, so the two variants are never present together.

---

## File Structure

- Create `layouts/_partials/home-ending.html`: homepage-only localized markup and fingerprinted module tag.
- Create `assets/js/home-ending.mjs`: progressive-enhancement state machine and return-to-top behavior.
- Create `tests/home-ending.test.mjs`: dependency-free unit tests for animation activation, fallbacks, and scrolling.
- Modify `layouts/home.html`: give the homepage a fragment target and render the ending after Popular posts.
- Modify `i18n/en.toml`: English lead, accessible complete thought, and return-link copy.
- Modify `i18n/zh.toml`: Chinese lead, accessible complete thought, and return-link copy.
- Modify `assets/css/site.css`: spacing, muted presentation, one-shot dot/link keyframes, and reduced-motion rules.
- Modify `tests/test_site.py`: generated-site and CSS contract tests.

### Task 1: Homepage-only localized markup

**Files:**
- Create: `layouts/_partials/home-ending.html`
- Modify: `layouts/home.html:15-29`
- Modify: `i18n/en.toml`
- Modify: `i18n/zh.toml`
- Test: `tests/test_site.py`

- [ ] **Step 1: Write the failing generated-site test**

Add this method beside `test_home_sections_are_ordered_title_only_and_language_local` in `tests/test_site.py`:

```python
    def test_escaping_thought_is_localized_home_only_and_base_path_safe(self):
        module_pattern = re.compile(
            r'<script(?=[^>]*\btype="module")'
            r'(?=[^>]*\bsrc="([^"]*home-ending[^"]*)")'
            r'(?=[^>]*\bintegrity="([^"]+)")[^>]*></script>'
        )
        expected = {
            "en": (
                "There was one more thing...",
                "↑ perhaps start over",
            ),
            "zh": (
                "好像还有件事……",
                "↑ 要不从头再来",
            ),
        }

        with TemporaryDirectory() as temporary:
            for name, base_url, base_path in (
                ("root", "https://example.test/", "/"),
                ("project", "https://example.test/example-blog/", "/example-blog/"),
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
                pages = {
                    "en": read_html(public, "index.html"),
                    "zh": read_html(public, "zh/index.html"),
                }

                for language, html in pages.items():
                    with self.subTest(build=name, language=language):
                        thought, return_label = expected[language]
                        self.assertEqual(
                            1,
                            len(re.findall(
                                r'<div\b[^>]*\sdata-home-ending(?:\s|>)',
                                html,
                            )),
                        )
                        self.assertIn('id="home-top"', html)
                        self.assertIn('data-home-ending-state="static"', html)
                        self.assertIn(f'aria-label="{thought}"', html)
                        self.assertIn(f'href="#home-top">{return_label}</a>', html)
                        self.assertEqual(3, html.count("data-home-ending-dot"))
                        self.assertLess(
                            html.index('data-home-section="popular"'),
                            html.index("data-home-ending"),
                        )
                        self.assertLess(
                            html.index("data-home-ending"),
                            html.index("<footer>"),
                        )
                        self.assertNotRegex(
                            html[html.index("data-home-ending"):html.index("<footer>")],
                            r"<(?:img|picture|video)\b",
                        )

                        modules = module_pattern.findall(html)
                        self.assertEqual(1, len(modules))
                        source, integrity = modules[0]
                        self.assertRegex(
                            source,
                            rf"^{re.escape(base_path)}js/"
                            r"home-ending\.[0-9a-f]{64}\.mjs$",
                        )
                        asset = public / urlsplit(source).path.removeprefix(base_path)
                        self.assertTrue(asset.is_file(), source)
                        expected_integrity = "sha256-" + base64.b64encode(
                            hashlib.sha256(asset.read_bytes()).digest()
                        ).decode("ascii")
                        self.assertEqual(expected_integrity, integrity)

                for relative in (
                    "p/shared-article/index.html",
                    "zh/p/shared-article/index.html",
                    "blog/index.html",
                    "zh/blog/index.html",
                    "tags/index.html",
                    "zh/tags/index.html",
                    "404.html",
                ):
                    with self.subTest(build=name, non_home=relative):
                        self.assertNotIn(
                            "data-home-ending",
                            read_html(public, relative),
                        )
```

- [ ] **Step 2: Run the generated-site test and verify it fails for the missing ending**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_escaping_thought_is_localized_home_only_and_base_path_safe -v
```

Expected: `FAIL` because neither homepage contains `data-home-ending`.

- [ ] **Step 3: Add the localized strings**

Append to `i18n/en.toml`:

```toml
[homeEndingLead]
other = "There was one more thing"
[homeEndingThought]
other = "There was one more thing..."
[homeEndingReturn]
other = "↑ perhaps start over"
```

Append to `i18n/zh.toml`:

```toml
[homeEndingLead]
other = "好像还有件事"
[homeEndingThought]
other = "好像还有件事……"
[homeEndingReturn]
other = "↑ 要不从头再来"
```

- [ ] **Step 4: Create the homepage-ending partial**

Create `layouts/_partials/home-ending.html` with:

```go-html-template
<div class="home-ending" data-home-ending data-home-ending-state="static">
  <p class="home-ending-thought" aria-label="{{ T "homeEndingThought" }}">
    <span aria-hidden="true">{{ T "homeEndingLead" }}<span class="home-ending-dots"><span data-home-ending-dot>.</span><span data-home-ending-dot>.</span><span data-home-ending-dot>.</span></span></span>
  </p>
  <a class="home-ending-return" data-home-ending-return href="#home-top">{{ T "homeEndingReturn" }}</a>
</div>
{{- $script := resources.Get "js/home-ending.mjs" | fingerprint "sha256" }}
<script type="module" src="{{ $script.RelPermalink }}" integrity="{{ $script.Data.Integrity }}"></script>
```

- [ ] **Step 5: Render the partial only from the homepage**

In `layouts/home.html`, change the opening content tag and append the partial after Popular posts:

```go-html-template
  <content id="home-top" class="home-content">
```

```go-html-template
    {{ partial "popular-posts.html" . }}
    {{ partial "home-ending.html" . }}
```

Create an empty `assets/js/home-ending.mjs` temporarily so Hugo can fingerprint the planned asset before Task 2 supplies its behavior.

- [ ] **Step 6: Run the generated-site test and verify it passes**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_escaping_thought_is_localized_home_only_and_base_path_safe -v
```

Expected: `OK` with one test passing.

- [ ] **Step 7: Commit the semantic homepage slice**

```bash
git add layouts/home.html layouts/_partials/home-ending.html assets/js/home-ending.mjs i18n/en.toml i18n/zh.toml tests/test_site.py
git commit -m "feat: add homepage escaping thought markup"
```

### Task 2: One-shot progressive enhancement

**Files:**
- Modify: `assets/js/home-ending.mjs`
- Create: `tests/home-ending.test.mjs`

- [ ] **Step 1: Write the failing interaction tests**

Create `tests/home-ending.test.mjs`:

```javascript
import assert from "node:assert/strict";
import test from "node:test";

import { mountHomeEnding } from "../assets/js/home-ending.mjs";


function endingDom() {
  const listeners = new Map();
  const link = {
    addEventListener(type, listener) {
      const active = listeners.get(type) ?? [];
      active.push(listener);
      listeners.set(type, active);
    },
    dispatch(type, event = {}) {
      for (const listener of listeners.get(type) ?? []) listener(event);
    },
  };
  const root = {
    dataset: { homeEndingState: "static" },
    querySelector(selector) {
      return selector === "[data-home-ending-return]" ? link : null;
    },
  };
  return { link, root };
}


function observerHarness() {
  const instances = [];
  class FakeIntersectionObserver {
    constructor(callback) {
      this.callback = callback;
      this.disconnected = false;
      this.observed = [];
      instances.push(this);
    }
    observe(element) {
      this.observed.push(element);
    }
    disconnect() {
      this.disconnected = true;
    }
    trigger(isIntersecting) {
      this.callback([{ isIntersecting }]);
    }
  }
  return { FakeIntersectionObserver, instances };
}


test("viewport entry starts the escaping thought only once", () => {
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
  assert.equal(instances[0].disconnected, true);
  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "playing");

  link.dispatch("animationend");
  assert.equal(root.dataset.homeEndingState, "complete");
  let prevented = false;
  link.dispatch("click", { preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  assert.deepEqual(scrollCalls, [{ top: 0, behavior: "smooth" }]);
});


test("reduced motion stays static and returns to top without smoothing", () => {
  const { link, root } = endingDom();
  const { FakeIntersectionObserver, instances } = observerHarness();
  const scrollCalls = [];
  mountHomeEnding(root, {
    IntersectionObserverImpl: FakeIntersectionObserver,
    matchMediaImpl: () => ({ matches: true }),
    scrollToImpl: (options) => scrollCalls.push(options),
  });

  assert.equal(root.dataset.homeEndingState, "reduced");
  assert.equal(instances.length, 0);
  let prevented = false;
  link.dispatch("click", { preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  assert.deepEqual(scrollCalls, [{ top: 0, behavior: "auto" }]);
});


test("missing IntersectionObserver exposes the completed fallback", () => {
  const { root } = endingDom();
  mountHomeEnding(root, {
    IntersectionObserverImpl: undefined,
    matchMediaImpl: () => ({ matches: false }),
    scrollToImpl: undefined,
  });

  assert.equal(root.dataset.homeEndingEnhanced, "true");
  assert.equal(root.dataset.homeEndingState, "complete");
});
```

- [ ] **Step 2: Run the Node test and verify the missing export fails**

Run:

```bash
node --test tests/home-ending.test.mjs
```

Expected: `FAIL` because `home-ending.mjs` does not export `mountHomeEnding`.

- [ ] **Step 3: Implement the minimal state machine**

Replace `assets/js/home-ending.mjs` with:

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

  root.dataset.homeEndingEnhanced = "true";
  returnLink?.addEventListener("animationend", () => {
    if (root.dataset.homeEndingState === "playing") {
      root.dataset.homeEndingState = "complete";
    }
  });
  if (returnLink && typeof scrollToImpl === "function") {
    returnLink.addEventListener("click", (event) => {
      event.preventDefault();
      scrollToImpl({
        top: 0,
        behavior: reducedMotion ? "auto" : "smooth",
      });
    });
  }

  if (reducedMotion) {
    root.dataset.homeEndingState = "reduced";
    return { observer: null };
  }
  if (typeof IntersectionObserverImpl !== "function") {
    root.dataset.homeEndingState = "complete";
    return { observer: null };
  }

  root.dataset.homeEndingState = "idle";
  let started = false;
  const observer = new IntersectionObserverImpl((entries) => {
    if (started || !entries.some(({ isIntersecting }) => isIntersecting)) return;
    started = true;
    observer.disconnect();
    root.dataset.homeEndingState = "playing";
  });
  observer.observe(root);
  return { observer };
}


function mountAll() {
  for (const root of document.querySelectorAll("[data-home-ending]")) {
    mountHomeEnding(root);
  }
}


if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll, { once: true });
  } else {
    mountAll();
  }
}
```

- [ ] **Step 4: Run the interaction tests and syntax check**

Run:

```bash
node --test tests/home-ending.test.mjs
node --check assets/js/home-ending.mjs
```

Expected: three tests pass and the syntax check exits with status 0.

- [ ] **Step 5: Commit the behavior slice**

```bash
git add assets/js/home-ending.mjs tests/home-ending.test.mjs
git commit -m "feat: animate the escaping thought once"
```

### Task 3: Quiet visual treatment and reduced motion

**Files:**
- Modify: `assets/css/site.css`
- Test: `tests/test_site.py`

- [ ] **Step 1: Write the failing CSS contract test**

Add this method beside the other CSS contract tests in `tests/test_site.py`:

```python
    def test_home_ending_has_large_gap_one_shot_motion_and_reduced_fallback(self):
        css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")

        self.assertRegex(
            css,
            r"\.home-ending\s*\{[^}]*"
            r"margin-block-start:\s*clamp\(8rem,\s*25vh,\s*15rem\);",
        )
        for name in (
            "home-ending-dot-one",
            "home-ending-dot-two",
            "home-ending-dot-three",
            "home-ending-return",
        ):
            self.assertEqual(1, css.count(f"@keyframes {name}"))
        self.assertIn("animation-iteration-count: 1", css)
        reduced = re.search(
            r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([\s\S]*)\}\s*$",
            css,
        )
        self.assertIsNotNone(reduced)
        self.assertIn("animation: none", reduced.group(1))
        self.assertIn("visibility: visible", reduced.group(1))
```

- [ ] **Step 2: Run the CSS contract test and verify it fails**

Run:

```bash
python3 -m unittest tests.test_site.GeneratedSiteTests.test_home_ending_has_large_gap_one_shot_motion_and_reduced_fallback -v
```

Expected: `FAIL` because `.home-ending` and its keyframes do not exist.

- [ ] **Step 3: Add the prototype styling**

Append to `assets/css/site.css`:

```css
.home-ending {
  color: var(--text-color-tertiary);
  margin-block-start: clamp(8rem, 25vh, 15rem);
  min-height: 6rem;
  padding-block-end: 2rem;
  text-align: center;
}

.home-ending-thought {
  margin: 0;
}

.home-ending-dots,
[data-home-ending-dot] {
  display: inline-block;
}

.home-ending-return {
  display: inline-block;
  font-size: 0.8em;
  margin-block-start: 1.25rem;
}

[data-home-ending-enhanced="true"][data-home-ending-state="idle"] .home-ending-return {
  opacity: 0;
  pointer-events: none;
  visibility: hidden;
}

[data-home-ending-state="playing"] [data-home-ending-dot],
[data-home-ending-state="playing"] .home-ending-return {
  animation-fill-mode: forwards;
  animation-iteration-count: 1;
}

[data-home-ending-state="playing"] [data-home-ending-dot]:nth-child(1) {
  animation-duration: 900ms;
  animation-name: home-ending-dot-one;
}

[data-home-ending-state="playing"] [data-home-ending-dot]:nth-child(2) {
  animation-delay: 280ms;
  animation-duration: 1s;
  animation-name: home-ending-dot-two;
}

[data-home-ending-state="playing"] [data-home-ending-dot]:nth-child(3) {
  animation-delay: 560ms;
  animation-duration: 1.1s;
  animation-name: home-ending-dot-three;
}

[data-home-ending-state="playing"] .home-ending-return {
  animation-delay: 1.8s;
  animation-duration: 600ms;
  animation-name: home-ending-return;
  opacity: 0;
  visibility: hidden;
}

[data-home-ending-state="complete"] [data-home-ending-dot] {
  opacity: 0;
}

[data-home-ending-state="complete"] .home-ending-return,
[data-home-ending-state="reduced"] .home-ending-return {
  opacity: 1;
  visibility: visible;
}

@keyframes home-ending-dot-one {
  to { opacity: 0; transform: translate(1.25rem, 0.35rem); }
}

@keyframes home-ending-dot-two {
  to { opacity: 0; transform: translate(2rem, 1rem); }
}

@keyframes home-ending-dot-three {
  to { opacity: 0; transform: translate(2.75rem, 1.75rem); }
}

@keyframes home-ending-return {
  from { opacity: 0; visibility: visible; }
  to { opacity: 1; visibility: visible; }
}

@media (prefers-reduced-motion: reduce) {
  [data-home-ending-dot],
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

- [ ] **Step 4: Run the focused homepage-ending tests**

Run:

```bash
python3 -m unittest \
  tests.test_site.GeneratedSiteTests.test_escaping_thought_is_localized_home_only_and_base_path_safe \
  tests.test_site.GeneratedSiteTests.test_home_ending_has_large_gap_one_shot_motion_and_reduced_fallback \
  -v
node --test tests/home-ending.test.mjs
```

Expected: five tests pass in total: two Python test methods and three Node cases.

- [ ] **Step 5: Commit the visual slice**

```bash
git add assets/css/site.css tests/test_site.py
git commit -m "style: finish escaping thought prototype"
```

### Task 4: Full verification and local review server

**Files:**
- Verify only; no expected source changes.

- [ ] **Step 1: Run all Python tests**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: every Python test passes with no failures or errors.

- [ ] **Step 2: Run all Node tests and JavaScript syntax checks**

Run:

```bash
node --test tests/*.test.mjs
node --check assets/js/home-ending.mjs
```

Expected: every Node test passes and the syntax check exits 0.

- [ ] **Step 3: Run repository validation and strict production builds**

Run:

```bash
python3 scripts/validate_interaction_ids.py content
hugo --cleanDestinationDir --panicOnWarning --noBuildLock --gc --environment production --destination /tmp/blog-escaping-thought-root --baseURL https://example.test/
python3 scripts/check_site.py /tmp/blog-escaping-thought-root --base-url https://example.test/
hugo --cleanDestinationDir --panicOnWarning --noBuildLock --gc --environment production --destination /tmp/blog-escaping-thought-project --baseURL https://example.test/example-blog/
python3 scripts/check_site.py /tmp/blog-escaping-thought-project --base-url https://example.test/example-blog/
```

Expected: the validator and both Hugo/checker pairs exit 0 with no warnings.

- [ ] **Step 4: Inspect the real interaction at desktop and mobile widths**

Start the development server:

```bash
hugo server --bind 127.0.0.1 --port 1313 --disableFastRender --noBuildLock
```

Open `http://127.0.0.1:1313/` and `http://127.0.0.1:1313/zh/`. At 1280×800 and 390×844 viewports, verify that the element is encountered only after a deliberate scroll beyond Popular posts, the dots run once without horizontal overflow, the link appears after the dots leave, the link returns to the top, and the global footer remains visually distinct. Reload with reduced motion emulated and verify static dots plus an immediately visible return link.

- [ ] **Step 5: Hand off prototype 1 for visual judgment**

Keep the local Hugo server running and provide the English and Chinese local URLs. Do not implement the train prototype until the user has reviewed this version in the site.
