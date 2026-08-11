import assert from "node:assert/strict";
import test from "node:test";

import { mountHomeEnding } from "../assets/js/home-ending.mjs";


function endingDom() {
  const listeners = new Map();
  const link = {
    addEventListener(type, listener) {
      const active = listeners.get(type) ?? [];
      active.push(listener);
      listeners.set(type, active);
    },
    dispatch(type, event = {}) {
      for (const listener of listeners.get(type) ?? []) listener(event);
    },
  };
  const root = {
    dataset: { homeEndingState: "static" },
    querySelector(selector) {
      return selector === "[data-home-ending-return]" ? link : null;
    },
  };
  return { link, root };
}


function observerHarness() {
  const instances = [];
  class FakeIntersectionObserver {
    constructor(callback) {
      this.callback = callback;
      this.disconnected = false;
      this.observed = [];
      instances.push(this);
    }
    observe(element) {
      this.observed.push(element);
    }
    disconnect() {
      this.disconnected = true;
    }
    trigger(isIntersecting) {
      this.callback([{ isIntersecting }]);
    }
  }
  return { FakeIntersectionObserver, instances };
}


test("return link re-arms the train only after a full viewport exit", () => {
  const { link, root } = endingDom();
  const { FakeIntersectionObserver, instances } = observerHarness();
  const scrollCalls = [];
  mountHomeEnding(root, {
    IntersectionObserverImpl: FakeIntersectionObserver,
    matchMediaImpl: () => ({ matches: false }),
    scrollToImpl: (options) => scrollCalls.push(options),
  });

  assert.equal(root.dataset.homeEndingEnhanced, "true");
  assert.equal(root.dataset.homeEndingState, "idle");
  assert.deepEqual(instances[0].observed, [root]);
  instances[0].trigger(false);
  assert.equal(root.dataset.homeEndingState, "idle");
  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "playing");
  assert.equal(instances[0].disconnected, false);
  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "playing");

  link.dispatch("animationend");
  assert.equal(root.dataset.homeEndingState, "complete");
  let prevented = false;
  link.dispatch("click", { preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  assert.deepEqual(scrollCalls, [{ top: 0, behavior: "smooth" }]);
  assert.equal(root.dataset.homeEndingState, "complete");

  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "complete");
  instances[0].trigger(false);
  assert.equal(root.dataset.homeEndingState, "idle");
  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "playing");
});


test("reduced motion stays static and returns to top without smoothing", () => {
  const { link, root } = endingDom();
  const { FakeIntersectionObserver, instances } = observerHarness();
  const scrollCalls = [];
  mountHomeEnding(root, {
    IntersectionObserverImpl: FakeIntersectionObserver,
    matchMediaImpl: () => ({ matches: true }),
    scrollToImpl: (options) => scrollCalls.push(options),
  });

  assert.equal(root.dataset.homeEndingState, "reduced");
  assert.equal(instances.length, 0);
  let prevented = false;
  link.dispatch("click", { preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  assert.deepEqual(scrollCalls, [{ top: 0, behavior: "auto" }]);
});


test("missing IntersectionObserver exposes the completed fallback", () => {
  const { root } = endingDom();
  mountHomeEnding(root, {
    IntersectionObserverImpl: undefined,
    matchMediaImpl: () => ({ matches: false }),
    scrollToImpl: undefined,
  });

  assert.equal(root.dataset.homeEndingEnhanced, "true");
  assert.equal(root.dataset.homeEndingState, "complete");
});
