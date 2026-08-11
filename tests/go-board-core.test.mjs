import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  reloadPristine,
  selectMainlineMove,
  selectPath,
} from "../assets/js/go-board-core.mjs";


globalThis.window = globalThis;
await import("../assets/vendor/besogo/js/besogo.js");
await import("../assets/vendor/besogo/js/gameRoot.js");
await import("../assets/vendor/besogo/js/editor.js");
await import("../assets/vendor/besogo/js/parseSgf.js");
await import("../assets/vendor/besogo/js/loadSgf.js");

const syntheticSgf = readFileSync(
  new URL("fixtures/go-board/synthetic.sgf", import.meta.url),
  "utf8",
);


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
