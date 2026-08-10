export function requireCount(data, entity) {
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("Kudos returned an invalid payload");
  }
  if (data.entity !== entity) {
    throw new Error("Kudos returned the wrong entity");
  }
  if (!Number.isSafeInteger(data.count) || data.count < 0) {
    throw new Error("Kudos returned an invalid count");
  }
  return data.count;
}


export function rankPopularPosts(candidates, limit = 5) {
  return [...candidates]
    .sort((left, right) => (
      right.count - left.count || left.recency - right.recency
    ))
    .slice(0, limit);
}


export async function loadPopularCounts({
  endpoint,
  candidates,
  fetchImpl = globalThis.fetch,
  timeoutMs = 5000,
}) {
  if (candidates.length < 2) return [...candidates];

  const baseUrl = endpoint.replace(/\/+$/, "");
  const controller = new AbortController();
  const timer = setTimeout(() => {
    controller.abort(new Error("Popular posts request timed out"));
  }, timeoutMs);

  try {
    const counted = await Promise.all(candidates.map(async (candidate) => {
      const url = `${baseUrl}/${encodeURIComponent(candidate.entity)}`;
      const response = await fetchImpl(url, {
        method: "GET",
        credentials: "omit",
        referrerPolicy: "no-referrer",
        signal: controller.signal,
      });
      let data;
      try {
        data = await response.json();
      } catch {
        throw new Error(`Kudos returned invalid JSON (${response.status})`);
      }
      if (!response.ok) {
        throw new Error(`Kudos request failed (${response.status})`);
      }
      return {
        ...candidate,
        count: requireCount(data, candidate.entity),
      };
    }));
    return rankPopularPosts(counted);
  } catch (error) {
    controller.abort();
    throw error;
  } finally {
    clearTimeout(timer);
  }
}


function setBusy(root, busy) {
  root.setAttribute("aria-busy", String(busy));
}


export function mountPopularPosts(
  root,
  fetchImpl = globalThis.fetch,
  logger = console,
) {
  const list = root.querySelector("[data-popular-list]");
  const status = root.querySelector("[data-popular-status]");
  const elements = [...root.querySelectorAll("[data-popular-candidate]")];
  const candidates = elements.map((element) => ({
    element,
    entity: element.dataset.entity,
    recency: Number(element.dataset.recency),
  }));

  async function load() {
    try {
      const ranked = await loadPopularCounts({
        endpoint: root.dataset.popularEndpoint,
        candidates,
        fetchImpl,
        timeoutMs: Number(root.dataset.popularTimeout),
      });
      const retained = new Set(ranked.map(({ element }) => element));
      for (const element of elements) {
        if (!retained.has(element)) element.remove();
      }
      for (const { element } of ranked) list.append(element);
      list.hidden = false;
      status.textContent = root.dataset.popularReadyLabel;
      root.dataset.popularState = "ready";
    } catch (error) {
      list.hidden = true;
      status.textContent = root.dataset.popularUnavailableLabel;
      status.classList.remove("visually-hidden");
      root.dataset.popularState = "error";
      logger.error("Failed to load popular posts", error);
    } finally {
      setBusy(root, false);
    }
  }

  return { ready: load() };
}


function mountAll() {
  for (const root of document.querySelectorAll("[data-popular-posts]")) {
    mountPopularPosts(root);
  }
}


if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll, { once: true });
  } else {
    mountAll();
  }
}
