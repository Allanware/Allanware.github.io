import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import * as goBoardCore from "../assets/js/go-board-core.mjs";

const {
  createSgfTextLoader,
  reloadPristine,
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
  const control = {
    disabled: false,
    addEventListener: (name, handler) => listeners.set(name, handler),
    click: () => {
      if (!control.disabled) listeners.get("click")();
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
  const move = { textContent: "" };
  const note = { hidden: true };
  const noteText = { textContent: "" };
  const status = { textContent: "Loading", dataset: {} };
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
    "[data-go-board-move]": move,
    "[data-go-board-note]": note,
    "[data-go-board-note-text]": noteText,
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
    move,
    note,
    noteText,
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

  const controller = mountGoBoard(dom.root, {
    besogo: boardBesogo(),
    loadSgfText: async () => { throw technicalError; },
    logger: { error: (...details) => logged.push(details) },
  });
  await controller.ready;

  assert.equal(dom.status.textContent, "无法加载棋谱。");
  assert.deepEqual(logged, [["无法加载棋谱。", technicalError]]);
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
  assert.equal(dom.returnButton.disabled, true);

  dom.previous.click();
  assert.equal(editor.getCurrent().moveNumber, 1);
  assert.equal(dom.returnButton.disabled, false);

  dom.returnButton.click();
  assert.notEqual(editor.getRoot(), publishedRoot);
  assert.equal(editor.getCurrent().moveNumber, 2);
  assert.equal(editor.getTool(), "navOnly");
  assert.equal(dom.returnButton.disabled, true);
  assert.equal(dom.tryButton.disabled, false);
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
