import assert from "node:assert/strict";
import test from "node:test";

import {
  selectMainlineMove,
  selectPath,
} from "../assets/js/go-board-core.mjs";


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


test("path selection uses one-based branch tokens and semantic move tokens", () => {
  const { root, branchNext } = authoredTree();

  assert.equal(selectPath(root, "N2B2N1"), branchNext);
});


test("selectors reject unavailable moves and branches", () => {
  const { root } = authoredTree();

  assert.throws(
    () => selectMainlineMove(root, 99),
    /Move 99 is not available/,
  );
  assert.throws(
    () => selectPath(root, "N2B3"),
    /Branch 3 is not available/,
  );
});
