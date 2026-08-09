// Kudos API contract: puinoib/kudos v0.2.0 at
// b449185be66d239555bf1242fec1169a0a09517f.


function requireEntity(data, entity) {
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("Kudos returned an invalid payload");
  }
  if (data.entity !== entity) {
    throw new Error("Kudos returned the wrong entity");
  }
  return data;
}


function requireCount(data, entity) {
  requireEntity(data, entity);
  if (!Number.isSafeInteger(data.count) || data.count < 0) {
    throw new Error("Kudos returned an invalid count");
  }
  return data.count;
}


function requireVoterState(data, entity) {
  requireEntity(data, entity);
  if (typeof data.hasKudos !== "boolean") {
    throw new Error("Kudos returned an invalid voter state");
  }
  return data.hasKudos;
}


export function createKudosClient({
  baseUrl,
  entity,
  fetchImpl = globalThis.fetch,
}) {
  const root = `${baseUrl.replace(/\/+$/, "")}/${encodeURIComponent(entity)}`;

  async function request(url, options = undefined) {
    const response = await fetchImpl(url, options);
    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error(`Kudos returned invalid JSON (${response.status})`);
    }
    if (!response.ok) {
      const message = (
        data !== null
        && typeof data === "object"
        && !Array.isArray(data)
        && typeof data.error === "string"
      ) ? data.error : `Kudos request failed (${response.status})`;
      throw new Error(message);
    }
    return data;
  }

  return {
    async load() {
      const [countData, stateData] = await Promise.all([
        request(root),
        request(`${root}/kudos`),
      ]);
      return {
        count: requireCount(countData, entity),
        hasKudos: requireVoterState(stateData, entity),
      };
    },

    async toggle(hasKudos) {
      const data = await request(`${root}/kudos`, {
        method: hasKudos ? "DELETE" : "POST",
      });
      return {
        count: requireCount(data, entity),
        hasKudos: requireVoterState(data, entity),
      };
    },
  };
}


function setBusy(root, busy) {
  root.setAttribute("aria-busy", String(busy));
}


export function renderKudos(root, state) {
  const button = root.querySelector("[data-kudos-button]");
  const count = root.querySelector("[data-kudos-count]");
  const status = root.querySelector("[data-kudos-status]");
  const hasKudos = state.hasKudos;
  count.textContent = String(state.count);
  button.classList.toggle("upvoted", hasKudos);
  button.setAttribute("aria-pressed", String(hasKudos));
  button.setAttribute(
    "aria-label",
    hasKudos ? root.dataset.removeLabel : root.dataset.addLabel,
  );
  status.textContent = "";
  root.dataset.kudosState = "ready";
  setBusy(root, false);
}


function renderLoadFailure(root) {
  const button = root.querySelector("[data-kudos-button]");
  root.querySelector("[data-kudos-count]").textContent = "—";
  root.querySelector("[data-kudos-status]").textContent = (
    root.dataset.unavailableLabel
  );
  button.classList.toggle("upvoted", false);
  button.removeAttribute("aria-pressed");
  button.setAttribute("aria-label", root.dataset.unavailableLabel);
  button.disabled = true;
  root.dataset.kudosState = "error";
  setBusy(root, false);
}


export function mountKudos(
  root,
  fetchImpl = globalThis.fetch,
  logger = console,
) {
  const button = root.querySelector("[data-kudos-button]");
  const status = root.querySelector("[data-kudos-status]");
  const client = createKudosClient({
    baseUrl: root.dataset.kudosEndpoint,
    entity: root.dataset.kudosEntity,
    fetchImpl,
  });
  let hasKudos = false;
  let loaded = false;
  let writing = false;

  root.hidden = false;
  button.disabled = true;
  setBusy(root, true);

  function render(state) {
    hasKudos = state.hasKudos;
    renderKudos(root, state);
  }

  async function load() {
    try {
      render(await client.load());
      loaded = true;
      button.disabled = false;
    } catch (error) {
      renderLoadFailure(root);
      logger.error("Failed to load Kudos", error);
    }
  }

  button.addEventListener("click", async () => {
    if (!loaded || writing) return;
    writing = true;
    button.disabled = true;
    status.textContent = "";
    root.dataset.kudosState = "writing";
    setBusy(root, true);
    try {
      render(await client.toggle(hasKudos));
    } catch (error) {
      status.textContent = root.dataset.updateFailedLabel;
      root.dataset.kudosState = "error";
      logger.error("Failed to update Kudos", error);
    } finally {
      writing = false;
      button.disabled = false;
      setBusy(root, false);
    }
  });

  return { ready: load() };
}


function mountAll() {
  for (const root of document.querySelectorAll("[data-kudos]")) {
    mountKudos(root);
  }
}


if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll, { once: true });
  } else {
    mountAll();
  }
}
