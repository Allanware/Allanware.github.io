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
  const returnButton = root.querySelector("[data-go-board-return]");
  const moveOutput = root.querySelector("[data-go-board-move]");
  const note = root.querySelector("[data-go-board-note]");
  const noteText = root.querySelector("[data-go-board-note-text]");
  const variations = root.querySelector("[data-go-board-variations]");
  const variationButtons = root.querySelector("[data-go-board-variation-buttons]");
  const variationStatus = root.querySelector("[data-go-board-variation-status]");
  const selector = selectorFor(root);
  let editor;
  let authoredTarget;
  let pristineSgf;

  for (const button of [previous, next, tryButton, returnButton]) {
    button.disabled = true;
  }
  setBusy(root, true);

  function fail(label, error) {
    status.textContent = label;
    status.dataset.state = "error";
    root.dataset.state = "error";
    setBusy(root, false);
    logger.error(label, error);
  }

  function sync() {
    const current = editor.getCurrent();
    const trying = editor.getTool() === "auto";
    previous.disabled = current.parent === null;
    next.disabled = current.children.length === 0;
    tryButton.disabled = trying;
    returnButton.disabled = !trying && current === authoredTarget;
    moveOutput.textContent = formatMove(
      root.dataset.moveTemplate,
      current.moveNumber,
    );
    noteText.textContent = current.comment || "";
    note.hidden = !current.comment;
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
      control.textContent = root.dataset.variationTemplate.replace("{label}", label);
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
        panels: [],
        tool: "navOnly",
        variants: 0,
        coord: "western",
        nowheel: true,
        resize: "none",
        realstones: false,
        shadows: "off",
      });
      editor = host.besogoEditor;
      loadSgfForReader({ besogo, editor, sgf: parsed });
      editor.setVariantStyle(0);
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
    previous.addEventListener("click", () => editor.prevNode(1));
    next.addEventListener("click", () => editor.nextNode(1));
    tryButton.addEventListener("click", () => {
      editor.setTool("auto");
      tryButton.disabled = true;
      returnButton.disabled = false;
      status.textContent = root.dataset.tryReadyLabel;
      status.dataset.state = "ready";
      root.dataset.state = "trying";
    });
    returnButton.addEventListener("click", () => {
      try {
        authoredTarget = reloadPristine({
          editor,
          sgfText: pristineSgf,
          selector,
          besogo,
        });
        editor.setVariantStyle(0);
        tryButton.disabled = false;
        returnButton.disabled = true;
        status.textContent = root.dataset.returnedLabel;
        status.dataset.state = "ready";
        root.dataset.state = "ready";
        sync();
      } catch (error) {
        fail(root.dataset.parseErrorLabel, error);
      }
    });

    tryButton.disabled = false;
    returnButton.disabled = true;
    status.textContent = root.dataset.readyLabel;
    status.dataset.state = "ready";
    root.dataset.state = "ready";
    setBusy(root, false);
    sync();
  }

  return { ready: initialize() };
}


function mountAll() {
  for (const root of document.querySelectorAll("[data-go-board]")) {
    mountGoBoard(root);
  }
}


if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll, { once: true });
  } else {
    mountAll();
  }
}
