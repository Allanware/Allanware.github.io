export function mountHomeEnding(root, options = {}) {
  const IntersectionObserverImpl = Object.hasOwn(options, "IntersectionObserverImpl")
    ? options.IntersectionObserverImpl
    : globalThis.IntersectionObserver;
  const matchMediaImpl = Object.hasOwn(options, "matchMediaImpl")
    ? options.matchMediaImpl
    : (typeof globalThis.matchMedia === "function"
      ? globalThis.matchMedia.bind(globalThis)
      : undefined);
  const locationImpl = Object.hasOwn(options, "locationImpl")
    ? options.locationImpl
    : globalThis.location;
  const reducedMotion = Boolean(
    matchMediaImpl?.("(prefers-reduced-motion: reduce)")?.matches,
  );
  const returnLink = root.querySelector("[data-home-ending-return]");
  let observer = null;

  root.dataset.homeEndingEnhanced = "true";
  returnLink?.addEventListener("animationend", () => {
    if (root.dataset.homeEndingState === "playing") {
      root.dataset.homeEndingState = "complete";
    }
  });
  returnLink?.addEventListener("click", (event) => {
    if (typeof locationImpl?.reload !== "function") return;
    event.preventDefault();
    locationImpl.hash = "#home-top";
    locationImpl.reload();
  });

  if (reducedMotion) {
    root.dataset.homeEndingState = "reduced";
    return { observer: null };
  }
  if (typeof IntersectionObserverImpl !== "function") {
    root.dataset.homeEndingState = "complete";
    return { observer: null };
  }

  root.dataset.homeEndingState = "idle";
  observer = new IntersectionObserverImpl((entries) => {
    if (!entries.some((entry) => entry.isIntersecting)) return;
    root.dataset.homeEndingState = "playing";
    observer.disconnect();
  });
  observer.observe(root);
  return { observer };
}


function mountAll() {
  for (const root of document.querySelectorAll("[data-home-ending]")) {
    mountHomeEnding(root);
  }
}


if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll, { once: true });
  } else {
    mountAll();
  }
}
