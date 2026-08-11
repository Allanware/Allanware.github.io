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


test("return link reloads the homepage at the top after one train journey", () => {
  const { link, root } = endingDom();
  const { FakeIntersectionObserver, instances } = observerHarness();
  const location = {
    hash: "",
    reloadCalls: 0,
    reload() {
      this.reloadCalls += 1;
    },
  };
  mountHomeEnding(root, {
    IntersectionObserverImpl: FakeIntersectionObserver,
    locationImpl: location,
    matchMediaImpl: () => ({ matches: false }),
  });

  assert.equal(root.dataset.homeEndingEnhanced, "true");
  assert.equal(root.dataset.homeEndingState, "idle");
  assert.deepEqual(instances[0].observed, [root]);
  instances[0].trigger(false);
  assert.equal(root.dataset.homeEndingState, "idle");
  instances[0].trigger(true);
  assert.equal(root.dataset.homeEndingState, "playing");
  assert.equal(instances[0].disconnected, true);

  link.dispatch("animationend");
  assert.equal(root.dataset.homeEndingState, "complete");
  let prevented = false;
  link.dispatch("click", { preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(location.hash, "#home-top");
  assert.equal(location.reloadCalls, 1);
});


test("reduced motion stays static and hard-reloads at the top", () => {
  const { link, root } = endingDom();
  const { FakeIntersectionObserver, instances } = observerHarness();
  const location = {
    hash: "",
    reloadCalls: 0,
    reload() {
      this.reloadCalls += 1;
    },
  };
  mountHomeEnding(root, {
    IntersectionObserverImpl: FakeIntersectionObserver,
    locationImpl: location,
    matchMediaImpl: () => ({ matches: true }),
  });

  assert.equal(root.dataset.homeEndingState, "reduced");
  assert.equal(instances.length, 0);
  let prevented = false;
  link.dispatch("click", { preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(location.hash, "#home-top");
  assert.equal(location.reloadCalls, 1);
});


test("missing IntersectionObserver exposes the completed fallback", () => {
  const { root } = endingDom();
  mountHomeEnding(root, {
    IntersectionObserverImpl: undefined,
    matchMediaImpl: () => ({ matches: false }),
  });

  assert.equal(root.dataset.homeEndingEnhanced, "true");
  assert.equal(root.dataset.homeEndingState, "complete");
});
