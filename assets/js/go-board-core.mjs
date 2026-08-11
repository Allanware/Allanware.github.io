export function selectMainlineMove(root, moveNumber) {
  if (!Number.isSafeInteger(moveNumber) || moveNumber < 0) {
    throw new RangeError("Move number must be a non-negative safe integer");
  }
  if (moveNumber === 0) return root;

  if (root.move && moveNumber === 1) return root;
  const remaining = moveNumber - (root.move ? 1 : 0);
  try {
    return advanceMainlineMoves(root, remaining);
  } catch {
    throw new RangeError(`Move ${moveNumber} is not available on the main line`);
  }
}


function advanceMainlineMoves(start, count) {
  let current = start;
  let remaining = count;
  while (remaining > 0) {
    do {
      if (current.children.length === 0) {
        throw new RangeError("Main line ended before the requested move");
      }
      current = current.children[0];
    } while (!current.move);
    remaining -= 1;
  }
  return current;
}


function advanceMainlineNodes(start, count) {
  let current = start;
  for (let index = 0; index < count; index += 1) {
    if (current.children.length === 0) {
      throw new RangeError("Main line ended before the requested node");
    }
    current = current.children[0];
  }
  return current;
}


export function selectPath(root, path) {
  if (!/^(?:N[0-9]+|B[1-9][0-9]*)+$/.test(path)) {
    throw new TypeError(`Invalid path selector: ${path}`);
  }

  let current = root;
  for (const match of path.matchAll(/([NB])([0-9]+)/g)) {
    const value = Number(match[2]);
    if (!Number.isSafeInteger(value)) {
      throw new RangeError(`Selector token ${match[0]} is too large`);
    }
    if (match[1] === "N") {
      try {
        current = advanceMainlineNodes(current, value);
      } catch {
        throw new RangeError(`Node token ${match[0]} exceeds the authored line`);
      }
    } else {
      const child = current.children[value - 1];
      if (!child) {
        throw new RangeError(`Branch ${value} is not available at this position`);
      }
      current = child;
    }
  }
  return current;
}


export function selectAuthoredNode(root, selector) {
  if (selector.kind === "path") {
    return selectPath(root, selector.value);
  }
  if (selector.kind !== "move" || !/^[0-9]+$/.test(String(selector.value))) {
    throw new TypeError("Invalid authored Go-board selector");
  }
  return selectMainlineMove(root, Number(selector.value));
}


export function reloadPristine({ editor, sgfText, selector, besogo }) {
  const parsed = besogo.parseSgf(sgfText);
  besogo.loadSgf(parsed, editor);
  editor.setTool("navOnly");
  const selected = selectAuthoredNode(editor.getRoot(), selector);
  editor.setCurrent(selected);
  return selected;
}
