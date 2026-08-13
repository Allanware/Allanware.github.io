const SYNTHETIC_PRE_MOVE_ROOT = Symbol("go-board synthetic pre-move root");
// Mirrors the root properties consumed by the pinned BesoGo loader. It ignores PL.
const ROOT_METADATA_IDS = new Set([
  "SZ", "ST",
  "PB", "BR", "BT", "PW", "WR", "WT",
  "HA", "KM", "RU", "TM", "OT",
  "DT", "EV", "GN", "PC", "RO",
  "GC", "ON", "RE", "AN", "CP", "SO", "US",
]);
const ROOT_SETUP_IDS = new Set(["AB", "AW", "AE"]);


export function validateSgfMoves(sgf) {
  const fileFormat = sgf.props.find((property) => property.id === "FF");
  if (!fileFormat || fileFormat.values.join().trim() !== "4") return;

  const sizeProperty = sgf.props.find((property) => property.id === "SZ");
  const size = parseBoardSize(sizeProperty?.values.join().trim() ?? "19");

  function validateNode(current) {
    for (const property of current.props) {
      if (property.id !== "B" && property.id !== "W") continue;
      if (property.values.length !== 1) {
        throw new TypeError(`SGF node has invalid ${property.id} coordinate`);
      }

      const coordinate = property.values[0];
      if (coordinate === "") continue;
      if (!/^[A-Za-z]{2}$/.test(coordinate)) {
        throw new TypeError(
          `SGF node has invalid ${property.id} coordinate "${coordinate}"`,
        );
      }

      const x = sgfLetterToNumber(coordinate[0]);
      const y = sgfLetterToNumber(coordinate[1]);
      if (x > size.x || y > size.y) {
        throw new RangeError(
          `SGF ${property.id} coordinate "${coordinate}" is outside the `
          + `${size.x}:${size.y} board`,
        );
      }
    }
    for (const child of current.children) validateNode(child);
  }

  validateNode(sgf);
}


function parseBoardSize(value) {
  const match = value.replace(/\s/g, "").match(/^(\d+)(?::(\d+))?$/);
  if (!match) return { x: 19, y: 19 };
  const x = Number(match[1]);
  const y = Number(match[2] ?? match[1]);
  if (x < 1 || x > 52 || y < 1 || y > 52) return { x: 19, y: 19 };
  return { x, y };
}


function sgfLetterToNumber(letter) {
  if (/[A-Z]/.test(letter)) return letter.charCodeAt(0) - 38;
  return letter.charCodeAt(0) - 96;
}


export function loadSgfForReader({ besogo, editor, sgf }) {
  const startsWithMove = sgf.props.some(
    (property) => property.id === "B" || property.id === "W",
  );
  let readerTree = sgf;
  if (startsWithMove) {
    const authoredRoot = {
      props: sgf.props.filter((property) => !ROOT_SETUP_IDS.has(property.id)),
      children: sgf.children,
    };
    readerTree = {
      props: sgf.props.filter(
        (property) => ROOT_METADATA_IDS.has(property.id)
          || ROOT_SETUP_IDS.has(property.id),
      ),
      children: [authoredRoot],
    };
  }

  besogo.loadSgf(readerTree, editor);
  const root = editor.getRoot();
  if (startsWithMove) root[SYNTHETIC_PRE_MOVE_ROOT] = true;
  return root;
}


export function selectMainlineMove(root, moveNumber) {
  if (!Number.isSafeInteger(moveNumber) || moveNumber < 0) {
    throw new RangeError("Move number must be a non-negative safe integer");
  }
  if (moveNumber === 0) {
    if (root.move) {
      throw new RangeError("Move 0 requires a pre-move root");
    }
    return root;
  }

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

  let current = root[SYNTHETIC_PRE_MOVE_ROOT] ? root.children[0] : root;
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
  validateSgfMoves(parsed);
  loadSgfForReader({ besogo, editor, sgf: parsed });
  editor.setTool("navOnly");
  const selected = selectAuthoredNode(editor.getRoot(), selector);
  editor.setCurrent(selected);
  return selected;
}


export function createSgfTextLoader(fetchImpl = globalThis.fetch) {
  const requests = new Map();
  return function loadSgfText(url) {
    if (!requests.has(url)) {
      requests.set(url, (async () => {
        const response = await fetchImpl(url);
        if (!response.ok) {
          throw new Error(`SGF request failed (${response.status})`);
        }
        return response.text();
      })());
    }
    return requests.get(url);
  };
}
