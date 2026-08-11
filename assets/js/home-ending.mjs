export function mountHomeEnding(root, options = {}) {
  const IntersectionObserverImpl = Object.hasOwn(options, "IntersectionObserverImpl")
    ? options.IntersectionObserverImpl
    : globalThis.IntersectionObserver;
  const matchMediaImpl = Object.hasOwn(options, "matchMediaImpl")
    ? options.matchMediaImpl
    : (typeof globalThis.matchMedia === "function"
      ? globalThis.matchMedia.bind(globalThis)
      : undefined);
  const scrollToImpl = Object.hasOwn(options, "scrollToImpl")
    ? options.scrollToImpl
    : (typeof globalThis.scrollTo === "function"
      ? globalThis.scrollTo.bind(globalThis)
      : undefined);
  const reducedMotion = Boolean(
    matchMediaImpl?.("(prefers-reduced-motion: reduce)")?.matches,
  );
  const returnLink = root.querySelector("[data-home-ending-return]");

  root.dataset.homeEndingEnhanced = "true";
  returnLink?.addEventListener("animationend", () => {
    if (root.dataset.homeEndingState === "playing") {
      root.dataset.homeEndingState = "complete";
    }
  });
  if (returnLink && typeof scrollToImpl === "function") {
    returnLink.addEventListener("click", (event) => {
      event.preventDefault();
      scrollToImpl({
        top: 0,
        behavior: reducedMotion ? "auto" : "smooth",
      });
    });
  }

  if (reducedMotion) {
    root.dataset.homeEndingState = "reduced";
    return { observer: null };
  }
  if (typeof IntersectionObserverImpl !== "function") {
    root.dataset.homeEndingState = "complete";
    return { observer: null };
  }

  root.dataset.homeEndingState = "idle";
  let started = false;
  const observer = new IntersectionObserverImpl((entries) => {
    if (started || !entries.some(({ isIntersecting }) => isIntersecting)) return;
    started = true;
    observer.disconnect();
    root.dataset.homeEndingState = "playing";
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
