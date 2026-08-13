# Go Board Multi-Position and Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show variation letters only at genuine forks, expand the example draft to three boards across two SGFs, and defer offscreen board construction without increasing the viewer beyond explicit performance budgets.

**Architecture:** Keep the pinned BesoGo sources unchanged. The site wrapper will synchronize BesoGo's existing variant style with the current node, schedule each shortcode instance through `IntersectionObserver`, and retain the existing URL-keyed SGF promise cache so editors remain independent while repeated resources share one request. Server-rendered hosts reserve their square layout before lazy mounting.

**Tech Stack:** Hugo 0.164 leaf bundles and shortcodes, vendored BesoGo JavaScript/SVG, browser `IntersectionObserver`, vanilla ES modules bundled by Hugo Pipes, Node's test runner, Python `unittest` and standard-library `gzip`.

---

### Task 1: Show automatic variation labels only at real forks

**Files:**
- Modify: `assets/js/go-board.mjs:94-109,259,287`
- Test: `tests/go-board-core.test.mjs:600-648`

- [ ] **Step 1: Write the failing fork-marker lifecycle test**

Add a focused runtime test using the existing synthetic SGF and real vendored editor:

```js
test("automatic board labels are enabled only at authored forks", async () => {
  const dom = boardDom({ kind: "path", value: "N3" });
  const controller = mountGoBoard(dom.root, {
    besogo: boardBesogo(),
    loadSgfText: async () => syntheticSgf,
    logger: { error() {} },
  });
  await controller.ready;

  const editor = dom.host.besogoEditor;
  const fork = editor.getCurrent();
  assert.equal(fork.children.length, 2);
  assert.equal(editor.getVariantStyle(), 0);

  editor.setCurrent(fork.children[0]);
  assert.equal(editor.getVariantStyle(), 2);

  dom.previous.click();
  assert.equal(editor.getCurrent(), fork);
  assert.equal(editor.getVariantStyle(), 0);

  editor.setCurrent(fork.children[1]);
  dom.returnButton.click();
  assert.equal(editor.getCurrent().children.length, 2);
  assert.equal(editor.getVariantStyle(), 0);
});
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```sh
node --test --test-name-pattern="automatic board labels" tests/go-board-core.test.mjs
```

Expected: FAIL because the current wrapper leaves variant style `0` after selecting a child with only one continuation.

- [ ] **Step 3: Add the minimal wrapper-level marker policy**

Add a helper inside `mountGoBoard` and call it from `sync` before rendering the contextual buttons:

```js
function syncVariantMarkers(current) {
  const desiredStyle = current.children.length > 1 ? 0 : 2;
  if (editor.getVariantStyle() !== desiredStyle) {
    editor.setVariantStyle(desiredStyle);
  }
}

function sync() {
  const current = editor.getCurrent();
  const trying = editor.getTool() === "auto";
  syncVariantMarkers(current);
  setTryControlsVisible(trying);
  // Keep the existing navigation, note, move, and variation-button updates.
}
```

The equality guard is required because `setVariantStyle` notifies editor listeners. Do not edit `assets/vendor/besogo/js/boardDisplay.js` or its checksum manifest.

Remove the two unconditional `editor.setVariantStyle(0)` calls from initialization and Return. The final `sync()` establishes the correct style for both fork and linear published targets without an unguarded listener notification. Extend the existing `Return restores the published selector after read-only navigation` test to assert that its linear move-2 target has variant style `2` before navigation and again after Return.

- [ ] **Step 4: Run the complete Go-board Node suite and verify GREEN**

Run:

```sh
node --test tests/go-board-core.test.mjs
```

Expected: all Go-board Node tests pass; the new test proves styles `0 → 2 → 0` across select, Previous, and Return.

- [ ] **Step 5: Commit the marker fix**

```sh
git add assets/js/go-board.mjs tests/go-board-core.test.mjs
git commit -m "fix: show Go variation labels only at forks"
```

### Task 2: Add the second SGF and three-board article example

**Files:**
- Copy: `/Users/allan/GitHub/blog/2026-7-26_pro.sgf` → `content/blog/go-game-review-2026-07-26/2026-7-26_pro.sgf`
- Modify: `content/blog/go-game-review-2026-07-26/index.en.md`
- Modify: `tests/test_go_board_authoring.py:13-115`
- Modify: `tests/go-board-core.test.mjs:22-34,181-214`

- [ ] **Step 1: Write failing asset-integrity and three-position tests**

Add the second supplied-record contract:

```python
PRO_SGF = BUNDLE / "2026-7-26_pro.sgf"
EXPECTED_PRO_SGF_SHA256 = (
    "4522758078cf8a367e446f981a2f52d3f9f5a91e75e0dc960da38b7100802363"
)

def test_second_sgf_is_the_unmodified_supplied_record(self):
    payload = PRO_SGF.read_bytes()
    self.assertEqual(4770, len(payload))
    self.assertEqual(
        EXPECTED_PRO_SGF_SHA256,
        hashlib.sha256(payload).hexdigest(),
    )

def test_example_uses_three_positions_across_two_records(self):
    boards = go_board_shortcodes(PAGE.read_text(encoding="utf-8"))
    self.assertEqual(
        [
            ("2026-7-26.sgf", "64"),
            ("2026-7-26.sgf", "80"),
            ("2026-7-26_pro.sgf", "36"),
        ],
        [(board["src"], board.get("move")) for board in boards],
    )
    self.assertEqual(
        [
            "2026-7-26.sgf — position after move 64.",
            "2026-7-26.sgf — position after move 80.",
            "2026-7-26_pro.sgf — position after move 36.",
        ],
        [board["caption"] for board in boards],
    )
    for board in boards:
        assert_valid_local_board(self, board, BUNDLE)
```

Extend the draft-inclusive build test to iterate over all shortcode attributes, verify each published SGF byte-for-byte, and assert that the three generated `<figure>` IDs are unique.

Add a runtime contract that parses the real bundle files and proves every published selector is a genuine fork:

```js
test("published review positions are genuine authored forks", () => {
  for (const [filename, move] of [
    ["2026-7-26.sgf", 64],
    ["2026-7-26.sgf", 80],
    ["2026-7-26_pro.sgf", 36],
  ]) {
    const sgfText = readFileSync(new URL(
      `../content/blog/go-game-review-2026-07-26/${filename}`,
      import.meta.url,
    ), "utf8");
    const editor = globalThis.besogo.makeEditor(19, 19);
    goBoardCore.loadSgfForReader({
      besogo: globalThis.besogo,
      editor,
      sgf: globalThis.besogo.parseSgf(sgfText),
    });
    const selected = goBoardCore.selectAuthoredNode(
      editor.getRoot(),
      { kind: "move", value: String(move) },
    );
    assert.equal(selected.children.length, 2, `${filename} move ${move}`);
  }
});
```

- [ ] **Step 2: Run the authoring tests and verify RED**

Run:

```sh
python3 -m unittest tests.test_go_board_authoring -v
node --test --test-name-pattern="published review positions" tests/go-board-core.test.mjs
```

Expected: FAIL because `2026-7-26_pro.sgf` is absent and the draft has only one board; the Node contract also cannot load the second supplied record yet.

- [ ] **Step 3: Copy the new SGF without rewriting it**

Run:

```sh
cp /Users/allan/GitHub/blog/2026-7-26_pro.sgf content/blog/go-game-review-2026-07-26/2026-7-26_pro.sgf
shasum -a 256 content/blog/go-game-review-2026-07-26/2026-7-26_pro.sgf
```

Expected SHA-256:

```text
4522758078cf8a367e446f981a2f52d3f9f5a91e75e0dc960da38b7100802363
```

- [ ] **Step 4: Expand the draft with two factual sections**

Keep the existing move-64 section but change its caption to `2026-7-26.sgf — position after move 64.`, then append:

```markdown
## A later position from the same SGF

The same record can be embedded again with a different starting position.

{{< go-board src="2026-7-26.sgf" move="80" caption="2026-7-26.sgf — position after move 80." >}}

## A position from a second SGF

A separate SGF in the same post bundle works the same way.

{{< go-board src="2026-7-26_pro.sgf" move="36" caption="2026-7-26_pro.sgf — position after move 36." >}}
```

Do not add strategic claims, a stub Chinese translation, or changes to either SGF.

- [ ] **Step 5: Run focused content and build verification**

Run:

```sh
python3 -m unittest tests.test_go_board_authoring tests.test_go_board -v
node --test --test-name-pattern="published review positions" tests/go-board-core.test.mjs
python3 scripts/validate_interaction_ids.py content
```

Expected: the focused Python and Node tests pass and interaction ID validation reports success.

- [ ] **Step 6: Commit the multi-position example**

```sh
git add content/blog/go-game-review-2026-07-26 tests/test_go_board_authoring.py tests/go-board-core.test.mjs
git commit -m "docs: add multi-position Go review example"
```

### Task 3: Defer offscreen board mounts and preserve an eager fallback

**Files:**
- Modify: `assets/js/go-board.mjs:314-326`
- Test: `tests/go-board-core.test.mjs`

- [ ] **Step 1: Write failing observer and shared-fetch scheduling tests**

Import new `mountAll` and `scheduleGoBoards` exports. Add a reusable fake-observer harness that captures each instance, callback, and options, then use it for the scheduling test:

```js
test("offscreen boards mount once near the viewport and defer distinct SGFs", async () => {
  const roots = [
    { dataset: { sgfUrl: "/p/game.sgf" } },
    { dataset: { sgfUrl: "/p/game.sgf" } },
    { dataset: { sgfUrl: "/p/pro.sgf" } },
  ];
  const requests = [];
  const pending = [];
  const load = createSgfTextLoader(async (url) => {
    requests.push(url);
    return { ok: true, text: async () => syntheticSgf };
  });
  let observer;

  class FakeIntersectionObserver {
    constructor(callback, options) {
      this.callback = callback;
      this.options = options;
      this.observed = [];
      this.unobserved = [];
      observer = this;
    }
    observe(root) { this.observed.push(root); }
    unobserve(root) { this.unobserved.push(root); }
  }

  const mounted = [];
  scheduleGoBoards(roots, {
    IntersectionObserver: FakeIntersectionObserver,
    mount(root) {
      mounted.push(root);
      pending.push(load(root.dataset.sgfUrl));
    },
  });

  assert.equal(observer.options.rootMargin, "400px 0px");
  assert.deepEqual(observer.observed, roots);
  assert.deepEqual(mounted, []);

  observer.callback(roots.slice(0, 2).map((target) => ({
    target,
    isIntersecting: true,
  })));
  observer.callback([{ target: roots[0], isIntersecting: true }]);
  await Promise.all(pending);
  assert.deepEqual(mounted, roots.slice(0, 2));
  assert.deepEqual(requests, ["/p/game.sgf"]);

  observer.callback([{ target: roots[2], isIntersecting: true }]);
  await Promise.all(pending);
  assert.deepEqual(requests, ["/p/game.sgf", "/p/pro.sgf"]);
  assert.deepEqual(observer.unobserved, roots);
});

test("boards mount eagerly when IntersectionObserver is unavailable", () => {
  const roots = [{}, {}, {}];
  const mounted = [];
  const observer = scheduleGoBoards(roots, {
    IntersectionObserver: null,
    mount: (root) => mounted.push(root),
  });
  assert.equal(observer, null);
  assert.deepEqual(mounted, roots);
});
```

Add an integration test with three `boardDom` fixtures. Give the first two roots `/p/game.sgf`, the third `/p/pro.sgf`, and every fixture a unique caption ID. Call exported `mountAll` with an injected document whose `querySelectorAll("[data-go-board]")` returns those roots, a fake observer, and a `mount` callback that calls the real `mountGoBoard` with one shared `createSgfTextLoader`. Intersect all three roots, await all three controller `ready` promises, and assert:

```js
assert.equal(returnedObserver, observer);
assert.deepEqual(requests, ["/p/game.sgf", "/p/pro.sgf"]);
assert.equal(new Set(doms.map((dom) => dom.host.besogoEditor)).size, 3);
for (const dom of doms) {
  assert.equal(dom.svgAttributes.get("role"), "img");
  assert.equal(dom.svgAttributes.get("aria-labelledby"), dom.root.dataset.captionId);
}
```

This exercises the real wrapper mount for three separate hosts, proves distinct editors and independently labelled SVG fixtures, and proves that the page bootstrap is routed through the observer scheduler while retaining the two-request cache behavior.

- [ ] **Step 2: Run the scheduling tests and verify RED**

Run:

```sh
node --test --test-name-pattern="offscreen boards|mount eagerly|independent board editors" tests/go-board-core.test.mjs
```

Expected: FAIL because `scheduleGoBoards` is not exported.

- [ ] **Step 3: Implement one-shot near-viewport scheduling**

Add this wrapper-only scheduler and route an injectable `mountAll` through it:

```js
export function scheduleGoBoards(roots, dependencies = {}) {
  const mount = dependencies.mount ?? mountGoBoard;
  const Observer = dependencies.IntersectionObserver === undefined
    ? globalThis.IntersectionObserver
    : dependencies.IntersectionObserver;
  const boards = Array.from(roots);

  if (typeof Observer !== "function") {
    for (const root of boards) mount(root);
    return null;
  }

  const mounted = new WeakSet();
  const observer = new Observer((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting || mounted.has(entry.target)) continue;
      mounted.add(entry.target);
      observer.unobserve(entry.target);
      mount(entry.target);
    }
  }, { rootMargin: "400px 0px" });

  for (const root of boards) observer.observe(root);
  return observer;
}

export function mountAll(dependencies = {}) {
  const documentObject = dependencies.document ?? globalThis.document;
  return scheduleGoBoards(
    documentObject.querySelectorAll("[data-go-board]"),
    dependencies,
  );
}
```

Change the DOM-ready registration to `document.addEventListener("DOMContentLoaded", () => mountAll(), { once: true })` so the event object is not mistaken for injected dependencies. The already-ready branch continues to call `mountAll()` directly.

Do not cache parsed editor trees or modify BesoGo. The existing module-level `loadSharedSgfText` remains the sole network cache.

- [ ] **Step 4: Run the full Go-board Node suite and verify GREEN**

Run:

```sh
node --test tests/go-board-core.test.mjs
```

Expected: all tests pass, repeated observer entries do not remount, and the third URL is not fetched until its own intersection.

- [ ] **Step 5: Commit lazy mounting**

```sh
git add assets/js/go-board.mjs tests/go-board-core.test.mjs
git commit -m "perf: defer offscreen Go boards"
```

### Task 4: Reserve board layout and enforce viewer budgets

**Files:**
- Modify: `assets/css/go-board.css:11-27,151-171`
- Modify: `tests/test_go_board.py`

- [ ] **Step 1: Add failing stable-layout checks and asset-budget guards**

Extend `GoBoardStyleTests` to require a server-rendered square host, a positioned shell, and an overlaid status:

```python
def test_unmounted_board_reserves_a_stable_square(self):
    css = (ROOT / "assets/css/go-board.css").read_text(encoding="utf-8")
    shell = re.search(r"\.go-board__shell\s*\{(?P<body>[^}]*)\}", css)
    host = re.search(r"\.go-board__host\s*\{(?P<body>[^}]*)\}", css)
    status = re.search(r"\.go-board__status\s*\{(?P<body>[^}]*)\}", css)
    self.assertIsNotNone(shell)
    self.assertIsNotNone(host)
    self.assertIsNotNone(status)
    self.assertRegex(shell.group("body"), r"position:\s*relative;")
    self.assertRegex(host.group("body"), r"aspect-ratio:\s*1;")
    self.assertRegex(host.group("body"), r"inline-size:\s*100%;")
    self.assertRegex(status.group("body"), r"position:\s*absolute;")
```

In the generated-site test, read the single built viewer JS and CSS assets and guard the approved budgets:

```python
import gzip

js_payload = next((public / "js").glob("go-board.*.js")).read_bytes()
css_payload = next((public / "css").glob("go-board.*.css")).read_bytes()
js_gzip = len(gzip.compress(js_payload, compresslevel=9, mtime=0))
css_gzip = len(gzip.compress(css_payload, compresslevel=9, mtime=0))
self.assertLessEqual(len(js_payload), 32_000)
self.assertLessEqual(js_gzip, 11_000)
self.assertLessEqual(len(css_payload), 5_000)
self.assertLessEqual(css_gzip, 1_500)
self.assertLessEqual(js_gzip + css_gzip, 12_500)
```

Keep the existing assertions that a page without the shortcode has zero viewer assets and a viewer page has exactly one self-hosted CSS and JS asset.

- [ ] **Step 2: Run the focused style/site test and verify RED**

Run:

```sh
python3 -m unittest tests.test_go_board.GoBoardStyleTests.test_unmounted_board_reserves_a_stable_square -v
```

Expected: FAIL because `.go-board__host` has no direct pre-mount aspect-ratio rule and the shell/status are not positioned.

- [ ] **Step 3: Reserve the host and overlay loading/error status**

Update the shell and host rules:

```css
.go-board__shell {
  inline-size: 100%;
  margin-inline: auto;
  max-width: 38rem;
  position: relative;
}

.go-board__host {
  aspect-ratio: 1;
  inline-size: 100%;
}

.go-board__host.besogo-container,
.go-board__host .besogo-board {
  aspect-ratio: 1;
  background: transparent;
  display: block;
  height: auto;
  width: 100%;
}

.go-board__status {
  inset: 50% auto auto 50%;
  margin: 0;
  max-width: calc(100% - 2rem);
  position: absolute;
  text-align: center;
  transform: translate(-50%, -50%);
  width: max-content;
}
```

Extend the existing ready-state visually hidden rule with `inset: auto; margin: -1px; transform: none;` so it remains a conventional one-pixel live region after mounting. Loading and error text stay centered in the reserved square.

- [ ] **Step 4: Run focused and integrated build checks**

Run:

```sh
python3 -m unittest tests.test_go_board tests.test_go_board_authoring -v
node --test tests/go-board-core.test.mjs
```

Expected: all focused tests pass and the generated assets remain below every budget.

- [ ] **Step 5: Commit the layout and budget policy**

```sh
git add assets/css/go-board.css tests/test_go_board.py
git commit -m "perf: stabilize lazy Go board layout"
```

### Task 5: Complete repository verification and live review

**Files:**
- Verify only; no planned product edits

- [ ] **Step 1: Run all repository checks**

Run:

```sh
python3 scripts/validate_interaction_ids.py content
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
actionlint .github/workflows/hugo.yml
git diff --check faf968a..HEAD
```

Expected: every command exits zero. The Node command must run where its temporary localhost test server is permitted.

- [ ] **Step 2: Run strict root and project-subpath builds**

Run:

```sh
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings --baseURL https://example.org/ \
  --destination /tmp/blog-go-board-root-final \
  --cacheDir /tmp/blog-go-board-root-cache
python3 scripts/check_site.py /tmp/blog-go-board-root-final \
  --base-url https://example.org/

hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings --buildDrafts \
  --baseURL https://example.github.io/example-blog/ \
  --destination /tmp/blog-go-board-project-final \
  --cacheDir /tmp/blog-go-board-project-cache
python3 scripts/check_site.py /tmp/blog-go-board-project-final \
  --base-url https://example.github.io/example-blog/
```

Expected: both builds complete without warnings and both site checks report `base-path verification passed`.

- [ ] **Step 3: Inspect final artifacts and supplied-file integrity**

Run:

```sh
shasum -a 256 \
  content/blog/go-game-review-2026-07-26/2026-7-26.sgf \
  content/blog/go-game-review-2026-07-26/2026-7-26_pro.sgf
git status --short --branch
```

Expected: hashes are respectively `829cceb4e5cc25b2d6a97104a76958c7431d98377e33d5d3c0031940bd158427` and `4522758078cf8a367e446f981a2f52d3f9f5a91e75e0dc960da38b7100802363`; the feature worktree is clean.

- [ ] **Step 4: Start the draft server and review the live page**

Start Hugo in a separate terminal or a yielded command session:

```sh
hugo server --buildDrafts --bind 127.0.0.1 --port 1314 \
  --disableFastRender --noBuildLock
```

Open `http://127.0.0.1:1314/p/go-game-review-2026-07-26/` and verify that:

- three boards appear as they approach the viewport;
- A/B labels appear at moves 64, 80, and 36;
- selecting a branch replaces automatic letters with the normal last-move marker;
- Previous restores the fork labels;
- navigation and Try on one board do not affect either other board;
- Return restores that board's published position.

If no browser controller is connected, report the limitation and leave the server URL available for user review; do not claim automated visual results.

- [ ] **Step 5: Request a final integrated review**

Have a fresh reviewer inspect the complete follow-up diff for specification compliance, accessibility, performance, test quality, and accidental vendor changes. Address any Critical or Important findings through a new RED/GREEN cycle before offering branch integration.
