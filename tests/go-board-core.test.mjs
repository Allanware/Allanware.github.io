import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import * as goBoardCore from "../assets/js/go-board-core.mjs";

const {
  createSgfTextLoader,
  nodeAtIndexPath,
  nodeIndexPath,
  reloadPristine,
  selectAuthoredNode,
  selectMainlineMove,
  selectPath,
} = goBoardCore;


globalThis.window = globalThis;
await import("../assets/vendor/besogo/js/besogo.js");
await import("../assets/vendor/besogo/js/gameRoot.js");
await import("../assets/vendor/besogo/js/editor.js");
await import("../assets/vendor/besogo/js/parseSgf.js");
await import("../assets/vendor/besogo/js/loadSgf.js");
const { mountAll, mountGoBoard, scheduleGoBoards } = await import(
  "../assets/js/go-board.mjs"
);

const syntheticSgf = readFileSync(
  new URL("fixtures/go-board/synthetic.sgf", import.meta.url),
  "utf8",
);
const authoringReadme = readFileSync(
  new URL("../README.md", import.meta.url),
  "utf8",
);
const contentRoot = fileURLToPath(new URL("../content/", import.meta.url));
const rootMoveSgf = "(;GM[1]FF[4]SZ[5]KM[6.5]C[Root move]B[aa](;W[bb])(;W[cc]))";
const rootMoveWithSetupSgf = "(;GM[1]FF[4]SZ[5]KM[6.5]AB[cc][ee]AW[dd]AE[ee]C[Root setup and move]B[aa];W[bb])";
const setupRootSgf = "(;GM[1]FF[4]SZ[5]KM[6.5]AB[cc]C[Setup root];B[aa](;W[bb])(;W[dd]))";


function goBoardShortcodes(text) {
  return Array.from(
    text.matchAll(/{{<\s*go-board\s+([\s\S]*?)\s*>}}/g),
    (shortcode) => Object.fromEntries(
      Array.from(
        shortcode[1].matchAll(/([a-zA-Z][\w-]*)="([^"]*)"/g),
        (attribute) => [attribute[1], attribute[2]],
      ),
    ),
  );
}


// Every board authored anywhere in content, discovered rather than listed, so
// editing or renaming a post does not invalidate these tests.
function authoredBoards() {
  return readdirSync(contentRoot, { recursive: true, withFileTypes: true })
    .filter((entry) => entry.isFile() && /^index\.[a-z]{2}\.md$/.test(entry.name))
    .flatMap((entry) => {
      const page = path.join(entry.parentPath ?? entry.path, entry.name);
      return goBoardShortcodes(readFileSync(page, "utf8")).map((attributes) => ({
        page,
        attributes,
        record: path.join(path.dirname(page), attributes.src),
      }));
    });
}


function readerEditor(sgfText) {
  const editor = globalThis.besogo.makeEditor(19, 19);
  goBoardCore.loadSgfForReader({
    besogo: globalThis.besogo,
    editor,
    sgf: globalThis.besogo.parseSgf(sgfText),
  });
  return editor;
}


function authoredSelector(attributes) {
  return "path" in attributes
    ? { kind: "path", value: attributes.path }
    : { kind: "move", value: attributes.move ?? "0" };
}


function node(name, move = null) {
  return { name, move, children: [], parent: null };
}


function append(parent, child) {
  child.parent = parent;
  parent.children.push(child);
  return child;
}


function authoredTree() {
  const root = node("root");
  const setup = append(root, node("setup"));
  const moveOne = append(setup, node("move-one", { color: -1 }));
  const note = append(moveOne, node("note"));
  const moveTwo = append(note, node("move-two", { color: 1 }));
  append(moveTwo, node("branch-one", { color: -1 }));
  const branchTwo = append(moveTwo, node("branch-two", { color: -1 }));
  const branchNote = append(branchTwo, node("branch-note"));
  const branchNext = append(branchNote, node("branch-next", { color: 1 }));
  return { root, moveTwo, branchNext };
}


test("main-line move selection ignores nodes without moves", () => {
  const { root, moveTwo } = authoredTree();

  assert.equal(selectMainlineMove(root, 2), moveTwo);
});


test("a moving SGF root cannot masquerade as semantic move zero", () => {
  const parsed = globalThis.besogo.parseSgf(rootMoveSgf);
  const editor = globalThis.besogo.makeEditor(19, 19);
  globalThis.besogo.loadSgf(parsed, editor);
  const movingRoot = editor.getRoot();

  assert.equal(movingRoot.moveNumber, 1);
  assert.throws(
    () => selectMainlineMove(movingRoot, 0),
    /pre-move root/,
  );
  assert.equal(selectMainlineMove(movingRoot, 1), movingRoot);
});


test("reader loading adds a non-mutating pre-move root without shifting authored paths", () => {
  assert.equal(typeof goBoardCore.loadSgfForReader, "function");
  const parsed = globalThis.besogo.parseSgf(rootMoveSgf);
  const authoredTree = JSON.stringify(parsed);
  const editor = globalThis.besogo.makeEditor(19, 19);

  goBoardCore.loadSgfForReader({
    besogo: globalThis.besogo,
    editor,
    sgf: parsed,
  });

  const preMove = editor.getRoot();
  const firstMove = selectMainlineMove(preMove, 1);
  assert.equal(JSON.stringify(parsed), authoredTree);
  assert.deepEqual(preMove.getSize(), { x: 5, y: 5 });
  assert.equal(editor.getGameInfo().KM, "6.5");
  assert.equal(preMove.move, null);
  assert.equal(preMove.moveNumber, 0);
  assert.equal(selectMainlineMove(preMove, 0), preMove);
  assert.equal(firstMove.moveNumber, 1);
  assert.deepEqual({ x: firstMove.move.x, y: firstMove.move.y }, { x: 1, y: 1 });
  assert.equal(selectMainlineMove(preMove, 2), firstMove.children[0]);
  assert.equal(selectPath(preMove, "N0"), firstMove);
  assert.equal(selectPath(preMove, "B2"), firstMove.children[1]);
  editor.setCurrent(firstMove);
  assert.deepEqual(editor.getVariants(), firstMove.children);
});


test("reader loading applies root setup before a same-node first move without duplicating deltas", () => {
  const parsed = globalThis.besogo.parseSgf(rootMoveWithSetupSgf);
  const authoredTree = JSON.stringify(parsed);
  const editor = globalThis.besogo.makeEditor(19, 19);

  goBoardCore.loadSgfForReader({
    besogo: globalThis.besogo,
    editor,
    sgf: parsed,
  });

  const preMove = editor.getRoot();
  const firstMove = preMove.children[0];
  assert.equal(JSON.stringify(parsed), authoredTree);
  assert.equal(preMove.getStone(3, 3), -1);
  assert.equal(preMove.getStone(4, 4), 1);
  assert.equal(preMove.getStone(5, 5), 0);
  assert.equal(preMove.getSetup(3, 3), "AB");
  assert.equal(preMove.getSetup(4, 4), "AW");
  assert.equal(preMove.getSetup(5, 5), false);
  assert.equal(firstMove.getSetup(3, 3), false);
  assert.equal(firstMove.moveNumber, 1);
  assert.deepEqual(
    { x: firstMove.move.x, y: firstMove.move.y, color: firstMove.move.color },
    { x: 1, y: 1, color: -1 },
  );
  assert.equal(firstMove.getStone(3, 3), -1);
  assert.equal(firstMove.getStone(4, 4), 1);
});


test("reader loading leaves an authored setup root and its paths unchanged", () => {
  assert.equal(typeof goBoardCore.loadSgfForReader, "function");
  const parsed = globalThis.besogo.parseSgf(setupRootSgf);
  const authoredTree = JSON.stringify(parsed);
  const editor = globalThis.besogo.makeEditor(19, 19);

  goBoardCore.loadSgfForReader({
    besogo: globalThis.besogo,
    editor,
    sgf: parsed,
  });

  const root = editor.getRoot();
  assert.equal(JSON.stringify(parsed), authoredTree);
  assert.equal(root.move, null);
  assert.equal(root.getStone(3, 3), -1);
  assert.equal(root.comment, "Setup root");
  assert.equal(selectMainlineMove(root, 0), root);
  assert.equal(selectPath(root, "N1B2"), root.children[0].children[1]);
});


test("path selection counts exact nodes and uses one-based branch tokens", () => {
  const { root, branchNext } = authoredTree();

  assert.equal(selectPath(root, "N4B2N2"), branchNext);
});


test("the documented exact-path example selects a branch off the mainline", () => {
  const advancedExample = goBoardShortcodes(authoringReadme).find(
    (example) => example.src && example.path && example.caption,
  );
  assert.ok(advancedExample, "README must document an exact-path example");

  const referenced = authoredBoards().find(
    ({ attributes }) => attributes.src === advancedExample.src,
  );
  if (!referenced) return; // the example names a record no post embeds

  const branch = advancedExample.path.match(/^(?<prefix>.*)B(?<index>\d+)$/);
  assert.ok(branch, "the exact-path example should end in a B branch token");
  assert.ok(Number(branch.groups.index) > 1, "B1 is the mainline child");

  const sgfText = readFileSync(referenced.record, "utf8");
  const root = readerEditor(sgfText).getRoot();
  const branchPoint = selectPath(root, branch.groups.prefix);
  const selected = selectPath(root, advancedExample.path);
  const mainline = selectPath(root, `${branch.groups.prefix}B1`);

  assert.ok(
    branchPoint.children.length >= Number(branch.groups.index),
    "the documented branch must exist in the record it names",
  );
  assert.equal(selected, branchPoint.children[Number(branch.groups.index) - 1]);
  assert.notEqual(selected, mainline);
});


test("every published board selector resolves against the record it names", () => {
  for (const { page, attributes, record } of authoredBoards()) {
    const selector = authoredSelector(attributes);
    const label = `${path.basename(page)} \u2192 ${attributes.src} ${
      JSON.stringify(selector)
    }`;
    const editor = readerEditor(readFileSync(record, "utf8"));
    const selected = selectAuthoredNode(editor.getRoot(), selector);

    assert.ok(selected, label);
    assert.equal(typeof selected.moveNumber, "number", label);
  }
});


test("selectors reject unavailable moves and branches", () => {
  const { root } = authoredTree();

  assert.throws(
    () => selectMainlineMove(root, 99),
    /Move 99 is not available/,
  );
  assert.throws(
    () => selectPath(root, "N4B3"),
    /Branch 3 is not available/,
  );
});


test("FF4 move validation accepts empty pass and rejects malformed or out-of-board points", () => {
  assert.equal(typeof goBoardCore.validateSgfMoves, "function");
  assert.doesNotThrow(() => goBoardCore.validateSgfMoves(
    globalThis.besogo.parseSgf("(;FF[4]SZ[5];B[];W[aa])"),
  ));
  assert.doesNotThrow(() => goBoardCore.validateSgfMoves(
    globalThis.besogo.parseSgf("(;FF[4]SZ[52];B[ZZ])"),
  ));
  assert.throws(
    () => goBoardCore.validateSgfMoves(
      globalThis.besogo.parseSgf("(;FF[4]SZ[5];B[aaa])"),
    ),
    /invalid B coordinate/,
  );
  assert.throws(
    () => goBoardCore.validateSgfMoves(
      globalThis.besogo.parseSgf("(;FF[4]SZ[5];W[fa])"),
    ),
    /outside the 5:5 board/,
  );
  assert.throws(
    () => goBoardCore.validateSgfMoves(
      globalThis.besogo.parseSgf("(;FF[4]SZ[5 : 5];W[fa])"),
    ),
    /outside the 5:5 board/,
  );
  assert.doesNotThrow(() => goBoardCore.validateSgfMoves(
    globalThis.besogo.parseSgf("(;FF[3]SZ[19];B[tt])"),
  ));
});


function loadSyntheticEditor() {
  const parsed = globalThis.besogo.parseSgf(syntheticSgf);
  const editor = globalThis.besogo.makeEditor(19, 19);
  globalThis.besogo.loadSgf(parsed, editor);
  return editor;
}


test("the vendored parser loads comments, pass, capture, setup, markup, and branches", () => {
  const editor = loadSyntheticEditor();
  const root = editor.getRoot();
  const capture = root.children[0];
  const pass = capture.children[0];
  const branchPoint = pass.children[0];

  assert.deepEqual(root.getSize(), { x: 5, y: 5 });
  assert.equal(root.comment, "Root <strong>unsafe</strong> comment");
  assert.equal(root.getStone(2, 3), -1);
  assert.equal(root.getStone(3, 3), 1);
  assert.equal(root.getMarkup(1, 1), 1);
  assert.equal(root.getMarkup(1, 2), 3);
  assert.equal(root.getMarkup(1, 3), 2);
  assert.equal(root.getMarkup(1, 4), 4);
  assert.equal(root.getMarkup(1, 5), "A");
  assert.equal(root.getMarkup(2, 1), 5);
  assert.equal(capture.move.captures, 1);
  assert.equal(capture.getStone(3, 3), 0);
  assert.deepEqual(
    { x: pass.move.x, y: pass.move.y },
    { x: 0, y: 0 },
  );
  assert.equal(branchPoint.move, null);
  assert.equal(branchPoint.children.length, 2);
  assert.equal(selectMainlineMove(root, 3), branchPoint.children[0]);
  assert.equal(selectPath(root, "N3B2N1"), branchPoint.children[1].children[0]);
});


test("pristine reload discards reader nodes, restores nav-only, and reapplies selector", () => {
  const editor = loadSyntheticEditor();
  const oldRoot = editor.getRoot();
  const pass = selectMainlineMove(oldRoot, 2);
  const readerNode = pass.makeChild();
  readerNode.playMove(1, 5, 0, true);
  pass.addChild(readerNode);
  editor.setCurrent(readerNode);
  editor.setTool("auto");

  const selected = reloadPristine({
    editor,
    sgfText: syntheticSgf,
    selector: { kind: "path", value: "N3B2" },
    besogo: globalThis.besogo,
  });

  assert.notEqual(editor.getRoot(), oldRoot);
  assert.equal(editor.getTool(), "navOnly");
  assert.equal(editor.getCurrent(), selected);
  assert.deepEqual(
    { x: selected.move.x, y: selected.move.y },
    { x: 5, y: 4 },
  );
  assert.equal(selectMainlineMove(editor.getRoot(), 2).children.length, 1);
});


test("index paths address nodes across a rebuilt tree and report unreachable ones", () => {
  const editor = loadSyntheticEditor();
  const root = editor.getRoot();
  const branch = selectPath(root, "N3B2");

  assert.deepEqual(nodeIndexPath(root, branch), [0, 0, 0, 1]);
  assert.equal(nodeAtIndexPath(root, [0, 0, 0, 1]), branch);
  assert.equal(nodeAtIndexPath(root, [0, 0, 0, 9]), null);
  assert.equal(nodeIndexPath(branch, root), null);
});


test("pristine reload restores the reader's departure point, not the selector", () => {
  const editor = loadSyntheticEditor();
  const departure = selectPath(editor.getRoot(), "N3B1");
  const restorePath = nodeIndexPath(editor.getRoot(), departure);

  const readerNode = departure.makeChild();
  readerNode.playMove(1, 5, 0, true);
  departure.addChild(readerNode);
  editor.setCurrent(readerNode);
  editor.setTool("auto");

  const authored = reloadPristine({
    editor,
    sgfText: syntheticSgf,
    selector: { kind: "move", value: "2" },
    besogo: globalThis.besogo,
    restorePath,
  });

  const current = editor.getCurrent();
  assert.equal(current.comment, "Main branch");
  assert.equal(current.children.length, 1);
  assert.equal(authored.moveNumber, 2);
  assert.notEqual(current, authored);
});


test("SGF text loading caches one fetch promise per resource URL", async () => {
  const requests = [];
  const load = createSgfTextLoader(async (url) => {
    requests.push(url);
    return {
      ok: true,
      status: 200,
      text: async () => syntheticSgf,
    };
  });

  const first = load("/p/viewer/synthetic.sgf");
  const second = load("/p/viewer/synthetic.sgf");

  assert.equal(first, second);
  assert.equal(await first, syntheticSgf);
  assert.deepEqual(requests, ["/p/viewer/synthetic.sgf"]);
});


function fakeIntersectionObserver() {
  const instances = [];

  class FakeIntersectionObserver {
    constructor(callback, options) {
      this.callback = callback;
      this.options = options;
      this.observed = [];
      this.unobserved = [];
      instances.push(this);
    }

    observe(root) {
      this.observed.push(root);
    }

    unobserve(root) {
      this.unobserved.push(root);
    }
  }

  return { FakeIntersectionObserver, instances };
}


test("offscreen boards mount only when they intersect and share URL fetches", async () => {
  const roots = [
    { dataset: { sgfUrl: "/p/game.sgf" } },
    { dataset: { sgfUrl: "/p/game.sgf" } },
    { dataset: { sgfUrl: "/p/pro.sgf" } },
  ];
  const requests = [];
  const mounted = [];
  const mountStates = [];
  const loader = createSgfTextLoader(async (url) => {
    requests.push(url);
    return { ok: true, status: 200, text: async () => syntheticSgf };
  });
  const { FakeIntersectionObserver, instances } = fakeIntersectionObserver();
  let observer;
  const mount = (root) => {
    mounted.push(root);
    mountStates.push([...observer.unobserved]);
    return loader(root.dataset.sgfUrl);
  };

  observer = scheduleGoBoards(roots, {
    IntersectionObserver: FakeIntersectionObserver,
    mount,
  });

  assert.equal(instances.length, 1);
  assert.equal(observer, instances[0]);
  assert.deepEqual(observer.options, { rootMargin: "400px 0px" });
  assert.deepEqual(observer.observed, roots);
  assert.deepEqual(mounted, []);
  assert.deepEqual(requests, []);

  observer.callback([{ target: roots[0], isIntersecting: false }]);
  assert.deepEqual(mounted, []);
  assert.deepEqual(requests, []);

  observer.callback([
    { target: roots[0], isIntersecting: true },
    { target: roots[1], isIntersecting: true },
  ]);
  assert.deepEqual(mounted, roots.slice(0, 2));
  assert.deepEqual(mountStates, [[roots[0]], [roots[0], roots[1]]]);
  assert.deepEqual(observer.unobserved, roots.slice(0, 2));
  assert.deepEqual(requests, ["/p/game.sgf"]);

  observer.callback([{ target: roots[0], isIntersecting: true }]);
  assert.deepEqual(mounted, roots.slice(0, 2));
  assert.deepEqual(requests, ["/p/game.sgf"]);
  assert.deepEqual(observer.unobserved, roots.slice(0, 2));
  assert.equal(mounted.includes(roots[2]), false);

  observer.callback([{ target: roots[2], isIntersecting: true }]);
  assert.deepEqual(mounted, roots);
  assert.deepEqual(observer.unobserved, roots);
  assert.deepEqual(requests, ["/p/game.sgf", "/p/pro.sgf"]);
  await Promise.all(mounted.map((root) => loader(root.dataset.sgfUrl)));
});


test("mount eagerly when IntersectionObserver is unavailable", () => {
  const roots = [{ dataset: {} }, { dataset: {} }, { dataset: {} }];
  const mounted = [];

  const observer = scheduleGoBoards(roots, {
    IntersectionObserver: null,
    mount: (root) => mounted.push(root),
  });

  assert.equal(observer, null);
  assert.deepEqual(mounted, roots);
});


function button() {
  const listeners = new Map();
  const attributes = new Map();
  const control = {
    disabled: false,
    focused: false,
    textContent: "",
    type: "",
    addEventListener: (name, handler) => listeners.set(name, handler),
    focus: () => { control.focused = true; },
    getAttribute: (name) => attributes.get(name),
    setAttribute: (name, value) => attributes.set(name, String(value)),
    click: () => {
      const listener = listeners.get("click");
      if (!control.disabled && listener) listener();
    },
  };
  return control;
}


function textInput() {
  const listeners = new Map();
  const attributes = new Map();
  const control = {
    value: "",
    focused: false,
    focus: () => { control.focused = true; },
    addEventListener: (name, handler) => listeners.set(name, handler),
    getAttribute: (name) => attributes.get(name),
    setAttribute: (name, value) => attributes.set(name, String(value)),
    press(key) {
      const listener = listeners.get("keydown");
      if (listener) listener({ key, preventDefault() {} });
    },
  };
  return control;
}


function boardDom(selector = { kind: "move", value: "2" }) {
  const attributes = new Map();
  const previous = button();
  const next = button();
  const tryButton = button();
  const tryControls = { hidden: true };
  const tryPoint = textInput();
  const tryStatus = { textContent: "" };
  tryButton.setAttribute("aria-controls", "go-board-fixture-try-controls");
  tryButton.setAttribute("aria-expanded", "false");
  tryButton.setAttribute("aria-pressed", "false");
  const move = { textContent: "" };
  const note = { hidden: true };
  const noteText = { textContent: "" };
  const status = { textContent: "Loading", dataset: {} };
  const variations = { hidden: true };
  const variationButtons = {
    children: [],
    replaceChildren(...children) {
      this.children = children;
    },
  };
  const variationStatus = { textContent: "" };
  const svgAttributes = new Map();
  const svg = {
    setAttribute: (name, value) => svgAttributes.set(name, value),
  };
  const hostAttributes = new Map();
  const hostListeners = new Map();
  const host = {
    besogoEditor: null,
    querySelector: (query) => query === "svg" ? svg : null,
    setAttribute: (name, value) => hostAttributes.set(name, String(value)),
    getAttribute: (name) => hostAttributes.get(name),
    addEventListener: (name, handler) => hostListeners.set(name, handler),
    press(key, modifiers = {}) {
      const listener = hostListeners.get("keydown");
      if (listener) listener({ key, preventDefault() {}, ...modifiers });
    },
  };
  const elements = {
    "[data-go-board-host]": host,
    "[data-go-board-status]": status,
    "[data-go-board-previous]": previous,
    "[data-go-board-next]": next,
    "[data-go-board-try]": tryButton,
    "[data-go-board-try-controls]": tryControls,
    "[data-go-board-try-point]": tryPoint,
    "[data-go-board-try-status]": tryStatus,
    "[data-go-board-move]": move,
    "[data-go-board-note]": note,
    "[data-go-board-note-text]": noteText,
    "[data-go-board-variations]": variations,
    "[data-go-board-variation-buttons]": variationButtons,
    "[data-go-board-variation-status]": variationStatus,
  };
  const root = {
    dataset: {
      sgfUrl: "/p/viewer/synthetic.sgf",
      selectorKind: selector.kind,
      selectorValue: selector.value,
      captionId: "go-board-fixture-caption",
      moveTemplate: "Move {move}",
      readyLabel: "Ready",
      tryReadyLabel: "Try mode",
      returnedLabel: "Returned",
      fetchErrorLabel: "Fetch failed",
      parseErrorLabel: "Parse failed",
      selectorErrorLabel: "Selector failed",
      variationTemplate: "Variation {label}",
      variationSelectedTemplate: "Variation {label} selected",
      tryLabel: "Try your own line",
      returnLabel: "Return to position",
      pointRequiredLabel: "Enter a point, for example D4.",
      pointUnavailableLabel: "That point cannot be played.",
      pointPlayedTemplate: "Played {coordinate}.",
    },
    ownerDocument: {
      createElement(name) {
        if (name === "button") return button();
        assert.fail(`Unexpected element: ${name}`);
      },
    },
    setAttribute: (name, value) => attributes.set(name, value),
    querySelector: (query) => elements[query],
  };
  return {
    root,
    host,
    status,
    previous,
    next,
    tryButton,
    tryControls,
    tryPoint,
    tryStatus,
    move,
    note,
    noteText,
    variations,
    variationButtons,
    variationStatus,
    attributes,
    hostAttributes,
    svgAttributes,
  };
}


function boardBesogo() {
  const createCalls = [];
  return {
    ...globalThis.besogo,
    create(host, options) {
      createCalls.push(options);
      const size = globalThis.besogo.parseSize(options.size);
      host.besogoEditor = globalThis.besogo.makeEditor(size.x, size.y);
      host.besogoEditor.setTool(options.tool);
      host.besogoEditor.setCoordStyle(options.coord);
    },
    createCalls,
  };
}


test("independent board editors mount through the page bootstrap", async () => {
  const fixtures = [boardDom(), boardDom(), boardDom()];
  const urls = ["/p/game.sgf", "/p/game.sgf", "/p/pro.sgf"];
  const captionIds = ["board-caption-one", "board-caption-two", "board-caption-three"];
  for (const [index, fixture] of fixtures.entries()) {
    fixture.root.dataset.sgfUrl = urls[index];
    fixture.root.dataset.captionId = captionIds[index];
  }

  const requests = [];
  const loader = createSgfTextLoader(async (url) => {
    requests.push(url);
    return { ok: true, status: 200, text: async () => syntheticSgf };
  });
  const besogo = boardBesogo();
  const controllers = [];
  const documentObject = {
    queries: [],
    querySelectorAll(query) {
      this.queries.push(query);
      return fixtures.map((fixture) => fixture.root);
    },
  };
  const { FakeIntersectionObserver, instances } = fakeIntersectionObserver();
  const mount = (root) => {
    const controller = mountGoBoard(root, {
      besogo,
      loadSgfText: loader,
      logger: { error() {} },
    });
    controllers.push(controller);
    return controller;
  };

  const observer = mountAll({
    document: documentObject,
    IntersectionObserver: FakeIntersectionObserver,
    mount,
  });

  assert.equal(observer, instances[0]);
  assert.deepEqual(documentObject.queries, ["[data-go-board]"]);
  observer.callback(fixtures.map((fixture) => ({
    target: fixture.root,
    isIntersecting: true,
  })));
  await Promise.all(controllers.map((controller) => controller.ready));

  assert.deepEqual(requests, ["/p/game.sgf", "/p/pro.sgf"]);
  const editors = fixtures.map((fixture) => fixture.host.besogoEditor);
  assert.notEqual(editors[0], editors[1]);
  assert.notEqual(editors[1], editors[2]);
  assert.notEqual(editors[0], editors[2]);
  for (const [index, fixture] of fixtures.entries()) {
    assert.equal(fixture.svgAttributes.get("role"), "img");
    assert.equal(
      fixture.svgAttributes.get("aria-labelledby"),
      captionIds[index],
    );
  }
});


test("board mounting parses and validates before creating BesoGo", async () => {
  const dom = boardDom({ kind: "move", value: "99" });
  const besogo = boardBesogo();

  const controller = mountGoBoard(dom.root, {
    besogo,
    loadSgfText: async () => syntheticSgf,
    logger: { error() {} },
  });
  await controller.ready;

  assert.equal(besogo.createCalls.length, 0);
  assert.equal(dom.status.textContent, "Selector failed");
  assert.equal(dom.attributes.get("aria-busy"), "false");
  assert.equal(dom.previous.disabled, true);
  assert.equal(dom.tryButton.disabled, true);
});


test("failure status uses only its localized label and logs technical detail", async () => {
  const dom = boardDom();
  const technicalError = new Error("SGF request failed (503)");
  const logged = [];
  dom.root.dataset.fetchErrorLabel = "无法加载棋谱。";
  dom.tryControls.hidden = false;
  dom.tryButton.setAttribute("aria-expanded", "true");

  const controller = mountGoBoard(dom.root, {
    besogo: boardBesogo(),
    loadSgfText: async () => { throw technicalError; },
    logger: { error: (...details) => logged.push(details) },
  });
  await controller.ready;

  assert.equal(dom.status.textContent, "无法加载棋谱。");
  assert.deepEqual(logged, [["无法加载棋谱。", technicalError]]);
  assert.equal(dom.tryControls.hidden, true);
  assert.equal(dom.tryButton.getAttribute("aria-expanded"), "false");
});


test("malformed FF4 coordinates fail with the localized parse label before mounting", async () => {
  const dom = boardDom();
  const besogo = boardBesogo();
  const logged = [];
  dom.root.dataset.parseErrorLabel = "无法读取棋谱。";

  const controller = mountGoBoard(dom.root, {
    besogo,
    loadSgfText: async () => "(;FF[4]SZ[5];B[zz])",
    logger: { error: (...details) => logged.push(details) },
  });
  await controller.ready;

  assert.equal(besogo.createCalls.length, 0);
  assert.equal(dom.status.textContent, "无法读取棋谱。");
  assert.match(logged[0][1].message, /outside the 5:5 board/);
});


test("the Try control toggles into local play and back to the published selector", async () => {
  const dom = boardDom();
  const besogo = boardBesogo();
  const controller = mountGoBoard(dom.root, {
    besogo,
    loadSgfText: async () => syntheticSgf,
    logger: { error() {} },
  });
  await controller.ready;

  const editor = dom.host.besogoEditor;
  const publishedRoot = editor.getRoot();
  assert.equal(editor.getCurrent().moveNumber, 2);
  assert.equal(editor.getVariantStyle(), 2);
  assert.equal(dom.tryButton.textContent, "Try your own line");
  assert.equal(dom.tryButton.getAttribute("aria-pressed"), "false");
  assert.equal(dom.tryControls.hidden, true);

  dom.previous.click();
  assert.equal(editor.getCurrent().moveNumber, 1);

  dom.tryButton.click();
  assert.equal(editor.getTool(), "auto");
  assert.equal(dom.tryControls.hidden, false);
  assert.equal(dom.tryButton.textContent, "Return to position");
  assert.equal(dom.tryButton.getAttribute("aria-pressed"), "true");
  assert.equal(dom.tryButton.getAttribute("aria-expanded"), "true");
  assert.equal(dom.tryPoint.focused, true);

  dom.tryButton.click();
  assert.notEqual(editor.getRoot(), publishedRoot);
  assert.equal(editor.getCurrent().moveNumber, 1);
  assert.equal(editor.getVariantStyle(), 2);
  assert.equal(editor.getTool(), "navOnly");
  assert.equal(dom.tryControls.hidden, true);
  assert.equal(dom.tryButton.textContent, "Try your own line");
  assert.equal(dom.tryButton.getAttribute("aria-pressed"), "false");
  assert.equal(dom.tryButton.disabled, false);
});


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

  // Returning lands back inside the branch, so the markers stay off there...
  editor.setCurrent(fork.children[1]);
  dom.tryButton.click();
  dom.tryButton.click();
  assert.equal(editor.getCurrent().children.length, 1);
  assert.equal(editor.getVariantStyle(), 2);

  // ...and come back on once the rebuilt fork is current again.
  dom.previous.click();
  assert.equal(editor.getCurrent().children.length, 2);
  assert.equal(editor.getVariantStyle(), 0);
});


test("named branch controls expose, choose, and identify authored A/B variations", async () => {
  const dom = boardDom();
  const controller = mountGoBoard(dom.root, {
    besogo: boardBesogo(),
    loadSgfText: async () => syntheticSgf,
    logger: { error() {} },
  });
  await controller.ready;

  const editor = dom.host.besogoEditor;
  assert.equal(dom.variations.hidden, true);
  dom.next.click();
  const branchPoint = editor.getCurrent();
  assert.equal(branchPoint.children.length, 2);
  assert.equal(dom.variations.hidden, false);
  assert.deepEqual(
    dom.variationButtons.children.map((control) => control.textContent),
    ["A", "B"],
  );
  assert.deepEqual(
    dom.variationButtons.children.map(
      (control) => control.getAttribute("aria-label"),
    ),
    ["Variation A", "Variation B"],
  );
  assert.deepEqual(
    dom.variationButtons.children.map(
      (control) => control.getAttribute("aria-pressed"),
    ),
    ["false", "false"],
  );

  dom.variationButtons.children[1].click();
  assert.equal(editor.getCurrent(), branchPoint.children[1]);
  assert.equal(dom.variationStatus.textContent, "Variation B selected");
  assert.deepEqual(
    dom.variationButtons.children.map(
      (control) => control.getAttribute("aria-pressed"),
    ),
    ["false", "true"],
  );
  assert.equal(dom.variationButtons.children[1].focused, true);

  editor.setCurrent(branchPoint);
  editor.setCurrent(branchPoint.children[0]);
  assert.equal(dom.variationStatus.textContent, "Variation A selected");
  assert.equal(
    dom.variationButtons.children[0].getAttribute("aria-pressed"),
    "true",
  );

  dom.tryButton.click();
  assert.equal(dom.variations.hidden, true);

  // Returning restores the chosen variation, so its chip comes back pressed.
  dom.tryButton.click();
  assert.equal(editor.getCurrent().moveNumber, 3);
  assert.equal(dom.variations.hidden, false);
  assert.equal(
    dom.variationButtons.children[0].getAttribute("aria-pressed"),
    "true",
  );
});


test("keyboard coordinate entry is disclosed only in Try mode", async () => {
  const dom = boardDom();
  dom.tryButton.setAttribute("aria-expanded", "true");
  const controller = mountGoBoard(dom.root, {
    besogo: boardBesogo(),
    loadSgfText: async () => syntheticSgf,
    logger: { error() {} },
  });
  await controller.ready;

  assert.equal(dom.tryControls.hidden, true);
  assert.equal(dom.tryButton.getAttribute("aria-expanded"), "false");
  assert.equal(
    dom.tryButton.getAttribute("aria-controls"),
    "go-board-fixture-try-controls",
  );

  dom.tryButton.click();
  assert.equal(dom.tryControls.hidden, false);
  assert.equal(dom.tryButton.getAttribute("aria-expanded"), "true");
  assert.equal(dom.tryPoint.focused, true);

  dom.tryPoint.value = "C2";
  dom.tryStatus.textContent = "old status";
  dom.tryButton.click();
  assert.equal(dom.tryControls.hidden, true);
  assert.equal(dom.tryButton.getAttribute("aria-expanded"), "false");
  assert.equal(dom.tryPoint.value, "");
  assert.equal(dom.tryStatus.textContent, "");
});


test("coordinate entry rejects empty and unplayable points and plays a legal one", async () => {
  const dom = boardDom();
  dom.root.dataset.pointRequiredLabel = "请输入落子点，例如 D4。";
  dom.root.dataset.pointUnavailableLabel = "该位置无法落子。";
  dom.root.dataset.pointPlayedTemplate = "已在 {coordinate} 落子。";
  const controller = mountGoBoard(dom.root, {
    besogo: boardBesogo(),
    loadSgfText: async () => syntheticSgf,
    logger: { error() {} },
  });
  await controller.ready;

  dom.tryButton.click();
  const editor = dom.host.besogoEditor;
  const startingPosition = editor.getCurrent();

  dom.tryPoint.press("Enter");
  assert.equal(editor.getCurrent(), startingPosition);
  assert.equal(dom.tryStatus.textContent, "请输入落子点，例如 D4。");

  dom.tryPoint.value = "Z9";
  dom.tryPoint.press("Enter");
  assert.equal(editor.getCurrent(), startingPosition);
  assert.equal(dom.tryStatus.textContent, "该位置无法落子。");

  dom.tryPoint.value = "B3";
  dom.tryPoint.press("Enter");
  assert.equal(editor.getCurrent(), startingPosition);
  assert.equal(dom.tryStatus.textContent, "该位置无法落子。");

  dom.tryPoint.value = "a1";
  dom.tryStatus.textContent = "";
  dom.tryPoint.press("Escape");
  assert.equal(editor.getCurrent(), startingPosition);
  assert.equal(dom.tryStatus.textContent, "");

  dom.tryPoint.focused = false;
  dom.tryPoint.press("Enter");
  assert.notEqual(editor.getCurrent(), startingPosition);
  assert.deepEqual(
    { x: editor.getCurrent().move.x, y: editor.getCurrent().move.y },
    { x: 1, y: 5 },
  );
  assert.equal(dom.move.textContent, "Move 3");
  assert.equal(dom.tryStatus.textContent, "已在 A1 落子。");
  assert.equal(dom.tryPoint.value, "");
  assert.equal(dom.tryPoint.focused, true);
});


test("root-move SGF starts at move zero and Return reloads its pristine pre-move tree", async () => {
  const dom = boardDom({ kind: "move", value: "0" });
  const besogo = boardBesogo();
  const authoredText = rootMoveSgf;
  const parseInputs = [];
  const parseSgf = besogo.parseSgf;
  besogo.parseSgf = (text) => {
    parseInputs.push(text);
    return parseSgf(text);
  };
  const controller = mountGoBoard(dom.root, {
    besogo,
    loadSgfText: async () => authoredText,
    logger: { error() {} },
  });
  await controller.ready;

  const editor = dom.host.besogoEditor;
  const initialRoot = editor.getRoot();
  assert.equal(editor.getCurrent(), initialRoot);
  assert.equal(editor.getCurrent().moveNumber, 0);
  assert.equal(editor.getCurrent().move, null);
  assert.equal(dom.move.textContent, "Move 0");
  assert.equal(initialRoot.children.length, 1);

  // Returning rebuilds the tree but keeps the reader where they were.
  dom.next.click();
  assert.equal(editor.getCurrent().moveNumber, 1);
  dom.tryButton.click();
  dom.tryButton.click();
  assert.notEqual(editor.getRoot(), initialRoot);
  assert.equal(editor.getCurrent().moveNumber, 1);

  const pristineRoot = editor.getRoot();
  const departure = editor.getCurrent();
  dom.tryButton.click();
  editor.click(5, 5, false, false);
  assert.equal(departure.children.length, 3);
  dom.tryButton.click();
  assert.notEqual(editor.getRoot(), pristineRoot);
  assert.equal(editor.getRoot().children.length, 1);
  assert.equal(editor.getCurrent().moveNumber, 1);
  assert.equal(editor.getCurrent().children.length, 2);
  assert.deepEqual(parseInputs, [authoredText, authoredText, authoredText]);
});


test("guided controls sync notes, enable local play, and restore pristine SGF", async () => {
  const dom = boardDom();
  const besogo = boardBesogo();
  const controller = mountGoBoard(dom.root, {
    besogo,
    loadSgfText: async () => syntheticSgf,
    logger: { error() {} },
  });
  await controller.ready;

  assert.deepEqual(besogo.createCalls, [{
    size: "5:5",
    tool: "navOnly",
    variants: 0,
    coord: "western",
    realstones: false,
    shadows: "off",
    nokeys: true,
  }]);
  assert.equal(dom.move.textContent, "Move 2");
  assert.equal(dom.noteText.textContent, "White passes");
  assert.equal(dom.previous.disabled, false);
  assert.equal(dom.next.disabled, false);
  assert.equal(dom.tryButton.disabled, false);
  assert.equal(dom.hostAttributes.get("tabindex"), "0");
  assert.equal(dom.svgAttributes.get("role"), "img");
  assert.equal(
    dom.svgAttributes.get("aria-labelledby"),
    "go-board-fixture-caption",
  );

  dom.tryButton.click();
  const editor = dom.host.besogoEditor;
  assert.equal(editor.getTool(), "auto");
  const authoredRoot = editor.getRoot();
  editor.click(1, 5, false, false);
  assert.equal(editor.getCurrent().parent.children.length, 2);

  dom.tryButton.click();
  assert.notEqual(editor.getRoot(), authoredRoot);
  assert.equal(editor.getTool(), "navOnly");
  assert.equal(editor.getCurrent().moveNumber, 2);
  assert.equal(editor.getCurrent().children.length, 1);
  assert.equal(dom.tryButton.disabled, false);
  assert.equal(dom.status.textContent, "Returned");

  dom.previous.click();
  assert.equal(dom.move.textContent, "Move 1");
});


test("returning from Try lands where the reader left, not at the authored position", async () => {
  const dom = boardDom();
  const besogo = boardBesogo();
  const controller = mountGoBoard(dom.root, {
    besogo,
    loadSgfText: async () => syntheticSgf,
    logger: { error() {} },
  });
  await controller.ready;

  // Walk away from the authored move 2 before trying anything.
  dom.next.click();
  dom.next.click();
  assert.equal(dom.move.textContent, "Move 3");
  assert.equal(dom.noteText.textContent, "Main branch");

  dom.tryButton.click();
  const editor = dom.host.besogoEditor;
  editor.click(1, 5, false, false);
  assert.equal(dom.move.textContent, "Move 4");

  dom.tryButton.click();
  assert.equal(dom.move.textContent, "Move 3");
  assert.equal(dom.noteText.textContent, "Main branch");
  assert.equal(editor.getCurrent().children.length, 1);

  // Home still goes to the authored position, so both destinations survive.
  dom.host.press("Home");
  assert.equal(dom.move.textContent, "Move 2");
  assert.equal(dom.noteText.textContent, "White passes");
});


test("the board host keymap steps, returns home, and runs to the end of the line", async () => {
  const dom = boardDom();
  const controller = mountGoBoard(dom.root, {
    besogo: boardBesogo(),
    loadSgfText: async () => syntheticSgf,
    logger: { error() {} },
  });
  await controller.ready;

  const editor = dom.host.besogoEditor;
  const authored = editor.getCurrent();
  assert.equal(authored.moveNumber, 2);

  dom.host.press("ArrowLeft");
  assert.equal(editor.getCurrent().moveNumber, 1);
  dom.host.press("ArrowRight");
  assert.equal(editor.getCurrent(), authored);

  dom.host.press("End");
  assert.equal(editor.getCurrent().children.length, 0);
  dom.host.press("Home");
  assert.equal(editor.getCurrent(), authored);

  // Keys the trimmed surface no longer binds must leave the position alone.
  dom.host.press("Delete");
  dom.host.press("PageDown");
  dom.host.press("ArrowDown");
  assert.equal(editor.getCurrent(), authored);
});
