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
        current = advanceMainlineMoves(current, value);
      } catch {
        throw new RangeError(`Move token ${match[0]} exceeds the authored line`);
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
