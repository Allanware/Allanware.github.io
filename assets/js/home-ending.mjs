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
  let observer = null;
  let armed = true;
  let waitingForExit = false;

  root.dataset.homeEndingEnhanced = "true";
  returnLink?.addEventListener("animationend", () => {
    if (root.dataset.homeEndingState === "playing") {
      root.dataset.homeEndingState = "complete";
    }
  });
  returnLink?.addEventListener("click", (event) => {
    if (observer) {
      armed = false;
      waitingForExit = true;
    }
    if (typeof scrollToImpl === "function") {
      event.preventDefault();
      scrollToImpl({
        top: 0,
        behavior: reducedMotion ? "auto" : "smooth",
      });
    }
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
    const isIntersecting = entries.some((entry) => entry.isIntersecting);
    if (!isIntersecting) {
      if (waitingForExit) {
        waitingForExit = false;
        armed = true;
        root.dataset.homeEndingState = "idle";
      }
      return;
    }
    if (!armed) return;
    armed = false;
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
