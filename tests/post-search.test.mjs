import assert from "node:assert/strict";
import test from "node:test";

import { mountPostSearch } from "../assets/js/post-search.mjs";

class FakeElement {
  constructor({ attributes = {}, dataset = {}, textContent = "" } = {}) {
    this.attributes = attributes;
    this.dataset = dataset;
    this.hidden = false;
    this.listeners = new Map();
    this.textContent = textContent;
    this.value = "";
  }

  addEventListener(type, listener) {
    this.listeners.set(type, listener);
  }

  dispatch(type) {
    this.listeners.get(type)?.();
  }

  getAttribute(name) {
    return this.attributes[name] ?? null;
  }
}

function createPostList() {
  const input = new FakeElement();
  const items = [
    new FakeElement({
      dataset: { postTitle: "Newer visible post", postYear: "2026" },
      textContent: "August 9, 2026 Newer visible post",
    }),
    new FakeElement({
      dataset: { postTitle: "Older visible post", postYear: "2024" },
      textContent: "January 2, 2024 Older visible post",
    }),
  ];
  const years = [
    new FakeElement({ dataset: { postYear: "2026" } }),
    new FakeElement({ dataset: { postYear: "2024" } }),
  ];
  const count = new FakeElement({ textContent: "2 posts" });
  const empty = new FakeElement({ textContent: "No matching posts" });
  empty.hidden = true;
  const status = new FakeElement({
    attributes: { role: "status" },
  });
  const single = {
    "[data-post-search]": input,
    "[data-post-count]": count,
    "[data-search-empty]": empty,
    "[data-search-status]": status,
  };
  const multiple = {
    "[data-post-item]": items,
    "[data-post-year].post-year": years,
  };
  const root = {
    dataset: {
      countOne: "{count} post",
      countMany: "{count} posts",
    },
    querySelector(selector) {
      return single[selector] ?? null;
    },
    querySelectorAll(selector) {
      return multiple[selector] ?? [];
    },
  };
  return { count, empty, input, items, root, status, years };
}

test("filters titles, hides empty years, and announces the singular count", () => {
  const { count, empty, input, items, root, status, years } = createPostList();
  mountPostSearch(root);

  input.value = "NEWER";
  input.dispatch("input");

  assert.deepEqual(items.map((item) => item.hidden), [false, true]);
  assert.deepEqual(years.map((year) => year.hidden), [false, true]);
  assert.equal(count.textContent, "1 post");
  assert.equal(empty.hidden, true);
  assert.equal(status.textContent, "1 post");
});

test("filters and announces results without a visible count", () => {
  const { empty, input, items, root, status, years } = createPostList();
  const querySelector = root.querySelector.bind(root);
  root.querySelector = (selector) =>
    selector === "[data-post-count]" ? null : querySelector(selector);
  mountPostSearch(root);

  input.value = "newer";
  input.dispatch("input");

  assert.deepEqual(items.map((item) => item.hidden), [false, true]);
  assert.deepEqual(years.map((year) => year.hidden), [false, true]);
  assert.equal(empty.hidden, true);
  assert.equal(status.textContent, "1 post");
});

test("rendered dates do not match and localized no-results text is announced", () => {
  const { count, empty, input, items, root, status, years } = createPostList();
  mountPostSearch(root);

  input.value = "August 9, 2026";
  input.dispatch("input");

  assert.deepEqual(items.map((item) => item.hidden), [true, true]);
  assert.deepEqual(years.map((year) => year.hidden), [true, true]);
  assert.equal(count.textContent, "0 posts");
  assert.equal(empty.hidden, false);
  assert.equal(status.getAttribute("role"), "status");
  assert.equal(status.textContent, "No matching posts");
});

test("title matching does not depend on the reader runtime locale", () => {
  const { input, items, root } = createPostList();
  items[0].dataset.postTitle = "The Miracle of Istanbul";
  const localeLowerCase = String.prototype.toLocaleLowerCase;
  String.prototype.toLocaleLowerCase = function localeSensitiveLowerCase() {
    return localeLowerCase.call(this, "tr");
  };

  try {
    mountPostSearch(root);
    input.value = "istanbul";
    input.dispatch("input");
  } finally {
    String.prototype.toLocaleLowerCase = localeLowerCase;
  }

  assert.deepEqual(items.map((item) => item.hidden), [false, true]);
});

test("a post list without a search input is ignored", () => {
  assert.doesNotThrow(() => mountPostSearch({ querySelector: () => null }));
});

test("project and post groups filter independently", () => {
  const projects = createPostList();
  const posts = createPostList();
  projects.root.dataset.countOne = "{count} project";
  projects.root.dataset.countMany = "{count} projects";
  projects.count.textContent = "2 projects";
  mountPostSearch(projects.root);
  mountPostSearch(posts.root);

  projects.input.value = "newer";
  projects.input.dispatch("input");

  assert.equal(projects.count.textContent, "1 project");
  assert.deepEqual(projects.items.map((item) => item.hidden), [false, true]);
  assert.equal(posts.count.textContent, "2 posts");
  assert.deepEqual(posts.items.map((item) => item.hidden), [false, false]);
});
