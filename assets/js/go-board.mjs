import "../vendor/besogo/js/besogo.js";
import "../vendor/besogo/js/boardDisplay.js";
import "../vendor/besogo/js/coord.js";
import "../vendor/besogo/js/editor.js";
import "../vendor/besogo/js/gameRoot.js";
import "../vendor/besogo/js/loadSgf.js";
import "../vendor/besogo/js/parseSgf.js";
import "../vendor/besogo/js/svgUtil.js";

import {
  createSgfTextLoader,
  loadSgfForReader,
  nodeIndexPath,
  reloadPristine,
  selectAuthoredNode,
  validateSgfMoves,
} from "./go-board-core.mjs";


const loadSharedSgfText = createSgfTextLoader();


function selectorFor(root) {
  return {
    kind: root.dataset.selectorKind,
    value: root.dataset.selectorValue,
  };
}


function setBusy(root, busy) {
  root.setAttribute("aria-busy", String(busy));
}


function formatMove(template, moveNumber) {
  return template.replace("{move}", String(moveNumber));
}


export function mountGoBoard(root, dependencies = {}) {
  const besogo = dependencies.besogo ?? globalThis.besogo;
  const loadSgfText = dependencies.loadSgfText ?? loadSharedSgfText;
  const logger = dependencies.logger ?? console;
  const host = root.querySelector("[data-go-board-host]");
  const status = root.querySelector("[data-go-board-status]");
  const previous = root.querySelector("[data-go-board-previous]");
  const next = root.querySelector("[data-go-board-next]");
  const tryButton = root.querySelector("[data-go-board-try]");
  const tryControls = root.querySelector("[data-go-board-try-controls]");
  const tryPoint = root.querySelector("[data-go-board-try-point]");
  const tryStatus = root.querySelector("[data-go-board-try-status]");
  const moveOutput = root.querySelector("[data-go-board-move]");
  const noteText = root.querySelector("[data-go-board-note-text]");
  const variations = root.querySelector("[data-go-board-variations]");
  const variationButtons = root.querySelector("[data-go-board-variation-buttons]");
  const variationStatus = root.querySelector("[data-go-board-variation-status]");
  const selector = selectorFor(root);
  let editor;
  let authoredTarget;
  let pristineSgf;
  let tryOrigin = null;

  for (const button of [previous, next, tryButton]) {
    button.disabled = true;
  }
  resetTryEntry();
  setTryControlsVisible(false);
  setBusy(root, true);

  function resetTryEntry() {
    tryPoint.value = "";
    tryStatus.textContent = "";
  }

  function setTryControlsVisible(visible) {
    tryControls.hidden = !visible;
    tryButton.setAttribute("aria-expanded", String(visible));
    tryButton.setAttribute("aria-pressed", String(visible));
    tryButton.textContent = visible
      ? root.dataset.returnLabel
      : root.dataset.tryLabel;
  }

  function fail(label, error) {
    resetTryEntry();
    setTryControlsVisible(false);
    status.textContent = label;
    status.dataset.state = "error";
    root.dataset.state = "error";
    setBusy(root, false);
    logger.error(label, error);
  }

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
    previous.disabled = current.parent === null;
    next.disabled = current.children.length === 0;
    moveOutput.textContent = formatMove(
      root.dataset.moveTemplate,
      current.moveNumber,
    );
    noteText.textContent = current.comment || "";
    renderVariations(current, trying);
  }

  function renderVariations(current, trying) {
    let choices = [];
    let selected = null;
    if (!trying && current.children.length > 1) {
      choices = current.children;
    } else if (!trying && current.parent && current.parent.children.length > 1) {
      choices = current.parent.children;
      selected = current;
    }

    variationButtons.replaceChildren();
    variationStatus.textContent = "";
    variations.hidden = choices.length < 2;
    if (variations.hidden) return;

    const controls = choices.map((choice, index) => {
      const label = String.fromCharCode("A".charCodeAt(0) + (index % 26));
      const control = root.ownerDocument.createElement("button");
      control.type = "button";
      control.textContent = label;
      control.setAttribute(
        "aria-label",
        root.dataset.variationTemplate.replace("{label}", label),
      );
      control.setAttribute("aria-pressed", String(choice === selected));
      control.addEventListener("click", () => {
        editor.setCurrent(choice);
        const refreshedControl = variationButtons.children[index];
        if (refreshedControl) refreshedControl.focus();
      });
      return control;
    });
    variationButtons.replaceChildren(...controls);

    if (selected) {
      const index = choices.indexOf(selected);
      const label = String.fromCharCode("A".charCodeAt(0) + (index % 26));
      variationStatus.textContent = root.dataset.variationSelectedTemplate.replace(
        "{label}",
        label,
      );
    }
  }

  function parsePoint(text, size) {
    const coordinates = besogo.coord.western(size.x, size.y);
    const match = /^([A-Za-z])\s*([0-9]{1,2})$/.exec(String(text).trim());
    if (!match) return null;
    const column = match[1].toUpperCase();
    const row = String(Number(match[2]));
    let x = 0;
    let y = 0;
    for (let index = 1; index <= size.x; index += 1) {
      if (coordinates.x[index] === column) x = index;
    }
    for (let index = 1; index <= size.y; index += 1) {
      if (coordinates.y[index] === row) y = index;
    }
    if (!x || !y) return null;
    return { x, y, label: `${coordinates.x[x]}${coordinates.y[y]}` };
  }

  function playTryPoint() {
    if (editor.getTool() !== "auto") return;
    if (!tryPoint.value.trim()) {
      tryStatus.textContent = root.dataset.pointRequiredLabel;
      return;
    }

    const size = editor.getRoot().getSize();
    const point = parsePoint(tryPoint.value, size);
    if (!point) {
      tryStatus.textContent = root.dataset.pointUnavailableLabel;
      return;
    }

    const before = editor.getCurrent();
    const beforeMove = before.move;
    editor.click(point.x, point.y, false, false);
    const after = editor.getCurrent();
    if (after === before && after.move === beforeMove) {
      tryStatus.textContent = root.dataset.pointUnavailableLabel;
      return;
    }

    tryStatus.textContent = root.dataset.pointPlayedTemplate.replace(
      "{coordinate}",
      point.label,
    );
    tryPoint.value = "";
    tryPoint.focus();
  }

  function handleBoardKey(event) {
    switch (event.key) {
      case "ArrowLeft":
        editor.prevNode(1);
        break;
      case "ArrowRight":
        editor.nextNode(1);
        break;
      case "Home":
        editor.setCurrent(authoredTarget);
        break;
      case "End": {
        let node = editor.getCurrent();
        while (node.children.length > 0) node = node.children[0];
        editor.setCurrent(node);
        break;
      }
      default:
        return;
    }
    event.preventDefault();
  }

  async function initialize() {
    try {
      pristineSgf = await loadSgfText(root.dataset.sgfUrl);
    } catch (error) {
      fail(root.dataset.fetchErrorLabel, error);
      return;
    }

    let parsed;
    let previewEditor;
    try {
      parsed = besogo.parseSgf(pristineSgf);
      validateSgfMoves(parsed);
      previewEditor = besogo.makeEditor(19, 19);
      loadSgfForReader({ besogo, editor: previewEditor, sgf: parsed });
    } catch (error) {
      fail(root.dataset.parseErrorLabel, error);
      return;
    }

    try {
      selectAuthoredNode(previewEditor.getRoot(), selector);
    } catch (error) {
      fail(root.dataset.selectorErrorLabel, error);
      return;
    }

    const size = previewEditor.getRoot().getSize();
    try {
      besogo.create(host, {
        size: `${size.x}:${size.y}`,
        tool: "navOnly",
        variants: 0,
        coord: "western",
        realstones: false,
        shadows: "off",
        nokeys: true,
      });
      editor = host.besogoEditor;
      loadSgfForReader({ besogo, editor, sgf: parsed });
      authoredTarget = selectAuthoredNode(editor.getRoot(), selector);
      editor.setCurrent(authoredTarget);
    } catch (error) {
      fail(root.dataset.parseErrorLabel, error);
      return;
    }

    const svg = host.querySelector("svg");
    if (svg) {
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-labelledby", root.dataset.captionId);
    }

    editor.addListener(sync);
    host.setAttribute("tabindex", "0");
    host.addEventListener("keydown", handleBoardKey);
    previous.addEventListener("click", () => editor.prevNode(1));
    next.addEventListener("click", () => editor.nextNode(1));
    tryPoint.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      playTryPoint();
    });
    tryButton.addEventListener("click", () => {
      if (editor.getTool() === "auto") {
        try {
          authoredTarget = reloadPristine({
            editor,
            sgfText: pristineSgf,
            selector,
            besogo,
            restorePath: tryOrigin,
          });
          tryOrigin = null;
          resetTryEntry();
          setTryControlsVisible(false);
          status.textContent = root.dataset.returnedLabel;
          status.dataset.state = "ready";
          root.dataset.state = "ready";
          sync();
        } catch (error) {
          fail(root.dataset.parseErrorLabel, error);
        }
        return;
      }
      tryOrigin = nodeIndexPath(editor.getRoot(), editor.getCurrent());
      resetTryEntry();
      editor.setTool("auto");
      status.textContent = root.dataset.tryReadyLabel;
      status.dataset.state = "ready";
      root.dataset.state = "trying";
      tryPoint.focus();
    });

    tryButton.disabled = false;
    status.textContent = root.dataset.readyLabel;
    status.dataset.state = "ready";
    root.dataset.state = "ready";
    setBusy(root, false);
    sync();
  }

  return { ready: initialize() };
}


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


if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => mountAll(), { once: true });
  } else {
    mountAll();
  }
}
