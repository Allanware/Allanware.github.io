import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import * as goBoardCore from "../assets/js/go-board-core.mjs";

const {
  createSgfTextLoader,
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
const { mountGoBoard } = await import("../assets/js/go-board.mjs");

const syntheticSgf = readFileSync(
  new URL("fixtures/go-board/synthetic.sgf", import.meta.url),
  "utf8",
);
const goReviewSgf = readFileSync(
  new URL(
    "../content/blog/go-game-review-2026-07-26/2026-7-26.sgf",
    import.meta.url,
  ),
  "utf8",
);
const authoringReadme = readFileSync(
  new URL("../README.md", import.meta.url),
  "utf8",
);
const rootMoveSgf = "(;GM[1]FF[4]SZ[5]KM[6.5]C[Root move]B[aa](;W[bb])(;W[cc]))";
const rootMoveWithSetupSgf = "(;GM[1]FF[4]SZ[5]KM[6.5]AB[cc][ee]AW[dd]AE[ee]C[Root setup and move]B[aa];W[bb])";
const setupRootSgf = "(;GM[1]FF[4]SZ[5]KM[6.5]AB[cc]C[Setup root];B[aa](;W[bb])(;W[dd]))";


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


test("the documented exact path resolves against the bundled Go review", () => {
  const advancedExample = Array.from(
    authoringReadme.matchAll(/{{<\s*go-board\s+([^>]+)>}}/g),
    (shortcode) => Object.fromEntries(
      Array.from(
        shortcode[1].matchAll(/([a-zA-Z][\w-]*)="([^"]*)"/g),
        (attribute) => [attribute[1], attribute[2]],
      ),
    ),
  ).find((example) => (
    example.src === "2026-7-26.sgf" && example.path && example.caption
  ));
  assert.ok(advancedExample, "README must include the bundled exact-path example");

  const parsed = globalThis.besogo.parseSgf(goReviewSgf);
  const editor = globalThis.besogo.makeEditor(19, 19);
  goBoardCore.loadSgfForReader({
    besogo: globalThis.besogo,
    editor,
    sgf: parsed,
  });

  const branchPoint = selectPath(editor.getRoot(), "N64");
  const selected = selectPath(editor.getRoot(), advancedExample.path);
  assert.equal(branchPoint.children.length, 2);
  assert.equal(selected, branchPoint.children[1]);
  assert.equal(selected.moveNumber, 65);
  assert.deepEqual(
    { x: selected.move.x, y: selected.move.y },
    { x: 2, y: 14 },
  );
});


test("published review positions preserve their authored forks", () => {
  const positions = [
    ["2026-7-26.sgf", "64"],
    ["2026-7-26.sgf", "80"],
    ["2026-7-26_pro.sgf", "36"],
  ];

  for (const [source, move] of positions) {
    const sgfText = readFileSync(
      new URL(`../content/blog/go-game-review-2026-07-26/${source}`, import.meta.url),
      "utf8",
    );
    const parsed = globalThis.besogo.parseSgf(sgfText);
    const editor = globalThis.besogo.makeEditor(19, 19);
    goBoardCore.loadSgfForReader({
      besogo: globalThis.besogo,
      editor,
      sgf: parsed,
    });

    const selected = selectAuthoredNode(editor.getRoot(), {
      kind: "move",
      value: move,
    });
    assert.equal(selected.children.length, 2, `${source} move ${move}`);
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


function select() {
  const control = {
    children: [],
    focused: false,
    value: "",
    focus: () => { control.focused = true; },
    replaceChildren(...children) {
      this.children = children;
      this.value = children[0]?.value ?? "";
    },
  };
  return control;
}


function boardDom(selector = { kind: "move", value: "2" }) {
  const attributes = new Map();
  const previous = button();
  const next = button();
  const tryButton = button();
  const returnButton = button();
  const tryControls = { hidden: true };
  const tryColumn = select();
  const tryRow = select();
  const playMoveButton = button();
  playMoveButton.type = "button";
  const tryStatus = { textContent: "" };
  tryButton.setAttribute("aria-controls", "go-board-fixture-try-controls");
  tryButton.setAttribute("aria-expanded", "false");
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
  const host = {
    besogoEditor: null,
    querySelector: (query) => query === "svg" ? svg : null,
  };
  const elements = {
    "[data-go-board-host]": host,
    "[data-go-board-status]": status,
    "[data-go-board-previous]": previous,
    "[data-go-board-next]": next,
    "[data-go-board-try]": tryButton,
    "[data-go-board-return]": returnButton,
    "[data-go-board-try-controls]": tryControls,
    "[data-go-board-try-column]": tryColumn,
    "[data-go-board-try-row]": tryRow,
    "[data-go-board-play-move]": playMoveButton,
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
      columnPlaceholder: "Choose column",
      rowPlaceholder: "Choose row",
      pointRequiredLabel: "Choose a column and row.",
      pointUnavailableLabel: "That point cannot be played.",
      pointPlayedTemplate: "Played {coordinate}.",
    },
    ownerDocument: {
      createElement(name) {
        if (name === "button") return button();
        if (name === "option") return { textContent: "", value: "" };
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
    returnButton,
    tryControls,
    tryColumn,
    tryRow,
    playMoveButton,
    tryStatus,
    move,
    note,
    noteText,
    variations,
    variationButtons,
    variationStatus,
    attributes,
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


test("Return restores the published selector after read-only navigation", async () => {
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
  assert.equal(dom.returnButton.disabled, true);

  dom.previous.click();
  assert.equal(editor.getCurrent().moveNumber, 1);
  assert.equal(dom.returnButton.disabled, false);

  dom.returnButton.click();
  assert.notEqual(editor.getRoot(), publishedRoot);
  assert.equal(editor.getCurrent().moveNumber, 2);
  assert.equal(editor.getVariantStyle(), 2);
  assert.equal(editor.getTool(), "navOnly");
  assert.equal(dom.returnButton.disabled, true);
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

  editor.setCurrent(fork.children[1]);
  dom.returnButton.click();
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
  dom.returnButton.click();
  assert.equal(editor.getCurrent().moveNumber, 2);
  assert.equal(dom.variations.hidden, true);
});


test("keyboard move controls expose western coordinates only in Try mode", async () => {
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
  assert.equal(dom.playMoveButton.type, "button");
  assert.deepEqual(
    dom.tryColumn.children.map((option) => [option.value, option.textContent]),
    [["", "Choose column"], ["1", "A"], ["2", "B"], ["3", "C"],
      ["4", "D"], ["5", "E"]],
  );
  assert.deepEqual(
    dom.tryRow.children.map((option) => [option.value, option.textContent]),
    [["", "Choose row"], ["1", "5"], ["2", "4"], ["3", "3"],
      ["4", "2"], ["5", "1"]],
  );

  dom.tryButton.click();
  assert.equal(dom.tryControls.hidden, false);
  assert.equal(dom.tryButton.getAttribute("aria-expanded"), "true");
  assert.equal(dom.tryColumn.focused, true);

  dom.tryColumn.value = "3";
  dom.tryRow.value = "4";
  dom.tryStatus.textContent = "old status";
  dom.returnButton.click();
  assert.equal(dom.tryControls.hidden, true);
  assert.equal(dom.tryButton.getAttribute("aria-expanded"), "false");
  assert.equal(dom.tryColumn.value, "");
  assert.equal(dom.tryRow.value, "");
  assert.equal(dom.tryStatus.textContent, "");
});


test("native Play move contains invalid choices and plays a legal intersection", async () => {
  const dom = boardDom();
  dom.root.dataset.pointRequiredLabel = "请选择列和行。";
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

  dom.playMoveButton.click();
  assert.equal(editor.getCurrent(), startingPosition);
  assert.equal(dom.tryStatus.textContent, "请选择列和行。");

  dom.tryColumn.value = "2";
  dom.tryRow.value = "3";
  dom.playMoveButton.click();
  assert.equal(editor.getCurrent(), startingPosition);
  assert.equal(dom.tryStatus.textContent, "该位置无法落子。");

  dom.tryColumn.value = "1";
  dom.tryRow.value = "5";
  dom.tryColumn.focused = false;
  dom.playMoveButton.click();
  assert.notEqual(editor.getCurrent(), startingPosition);
  assert.deepEqual(
    { x: editor.getCurrent().move.x, y: editor.getCurrent().move.y },
    { x: 1, y: 5 },
  );
  assert.equal(dom.move.textContent, "Move 3");
  assert.equal(dom.tryStatus.textContent, "已在 A1 落子。");
  assert.equal(dom.tryColumn.value, "");
  assert.equal(dom.tryRow.value, "");
  assert.equal(dom.tryColumn.focused, true);
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

  dom.next.click();
  assert.equal(editor.getCurrent().moveNumber, 1);
  assert.equal(dom.returnButton.disabled, false);
  dom.returnButton.click();
  assert.notEqual(editor.getRoot(), initialRoot);
  assert.equal(editor.getCurrent().moveNumber, 0);

  const pristineRoot = editor.getRoot();
  dom.tryButton.click();
  editor.click(3, 3, false, false);
  assert.equal(pristineRoot.children.length, 2);
  dom.returnButton.click();
  assert.notEqual(editor.getRoot(), pristineRoot);
  assert.equal(editor.getRoot().children.length, 1);
  assert.equal(editor.getCurrent().moveNumber, 0);
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
    panels: [],
    tool: "navOnly",
    variants: 0,
    coord: "western",
    nowheel: true,
    resize: "none",
    realstones: false,
    shadows: "off",
  }]);
  assert.equal(dom.move.textContent, "Move 2");
  assert.equal(dom.noteText.textContent, "White passes");
  assert.equal(dom.note.hidden, false);
  assert.equal(dom.previous.disabled, false);
  assert.equal(dom.next.disabled, false);
  assert.equal(dom.tryButton.disabled, false);
  assert.equal(dom.returnButton.disabled, true);
  assert.equal(dom.svgAttributes.get("role"), "img");
  assert.equal(
    dom.svgAttributes.get("aria-labelledby"),
    "go-board-fixture-caption",
  );

  dom.tryButton.click();
  const editor = dom.host.besogoEditor;
  assert.equal(editor.getTool(), "auto");
  assert.equal(dom.tryButton.disabled, true);
  assert.equal(dom.returnButton.disabled, false);
  const authoredRoot = editor.getRoot();
  editor.click(1, 5, false, false);
  assert.equal(editor.getCurrent().parent.children.length, 2);

  dom.returnButton.click();
  assert.notEqual(editor.getRoot(), authoredRoot);
  assert.equal(editor.getTool(), "navOnly");
  assert.equal(editor.getCurrent().moveNumber, 2);
  assert.equal(editor.getCurrent().children.length, 1);
  assert.equal(dom.tryButton.disabled, false);
  assert.equal(dom.returnButton.disabled, true);
  assert.equal(dom.status.textContent, "Returned");

  dom.previous.click();
  assert.equal(dom.move.textContent, "Move 1");
});
