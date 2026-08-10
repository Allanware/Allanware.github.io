import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  loadPopularCounts,
  mountPopularPosts,
  rankPopularPosts,
} from "../assets/js/popular-posts.mjs";


function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}


function jsonResponse(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}


function invalidJsonResponse(status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => { throw new SyntaxError("invalid JSON"); },
  };
}


function popularDom(size = 6) {
  const rootAttributes = new Map([["aria-busy", "true"]]);
  const statusWrites = [];
  const removedStatusClasses = [];
  let statusText = "Loading popular posts";

  const status = {
    classList: {
      remove(name) {
        removedStatusClasses.push(name);
      },
    },
    get textContent() {
      return statusText;
    },
    set textContent(value) {
      statusText = value;
      statusWrites.push(value);
    },
  };

  const list = {
    hidden: true,
    children: [],
    append(element) {
      const currentIndex = this.children.indexOf(element);
      if (currentIndex !== -1) this.children.splice(currentIndex, 1);
      this.children.push(element);
      element.parentElement = this;
    },
    removeChild(element) {
      const index = this.children.indexOf(element);
      if (index !== -1) this.children.splice(index, 1);
      element.parentElement = null;
    },
  };

  for (let recency = 0; recency < size; recency += 1) {
    const element = {
      dataset: {
        entity: `post:item-${recency}`,
        recency: String(recency),
      },
      parentElement: list,
      remove() {
        this.parentElement?.removeChild(this);
      },
    };
    list.children.push(element);
  }

  const root = {
    dataset: {
      popularEndpoint: "https://kudos.example.test/",
      popularTimeout: "5000",
      popularReadyLabel: "Popular posts loaded",
      popularUnavailableLabel: "Popular posts are temporarily unavailable",
      popularState: "loading",
    },
    querySelector(selector) {
      return {
        "[data-popular-list]": list,
        "[data-popular-status]": status,
      }[selector];
    },
    querySelectorAll(selector) {
      return selector === "[data-popular-candidate]"
        ? [...list.children]
        : [];
    },
    setAttribute(name, value) {
      rootAttributes.set(name, value);
    },
  };

  return {
    list,
    removedStatusClasses,
    root,
    rootAttributes,
    status,
    statusWrites,
  };
}


test("popular markup has one accessible loading status and a sibling noscript fallback", () => {
  const partial = readFileSync(
    new URL("../layouts/_partials/popular-posts.html", import.meta.url),
    "utf8",
  );
  const english = readFileSync(
    new URL("../i18n/en.toml", import.meta.url),
    "utf8",
  );

  assert.match(partial, /data-popular-posts[\s\S]*aria-busy="true"/);
  assert.match(partial, /<ol\b[^>]*data-popular-list[^>]*hidden/);
  assert.equal(partial.match(/role="status"/g)?.length, 1);
  assert.equal(partial.match(/aria-live="polite"/g)?.length, 1);
  assert.equal(partial.match(/aria-atomic="true"/g)?.length, 1);
  assert.match(partial, /data-popular-status[^>]*>[\s\S]*T "popularLoading"/);
  assert.match(
    english,
    /\[popularLoading\]\s*other = "Loading popular posts"/,
  );
  assert.match(
    partial,
    /<div\b[^>]*data-popular-posts[\s\S]*?<\/div>\s*<noscript\b/,
  );
  assert.equal(partial.match(/<noscript\b/g)?.length, 1);
});


test("rankPopularPosts orders by count, breaks ties by recency, and keeps five", () => {
  const candidates = [
    { entity: "post:newest", recency: 0, count: 7 },
    { entity: "post:tie-new", recency: 1, count: 12 },
    { entity: "post:tie-old", recency: 2, count: 12 },
    { entity: "post:middle", recency: 3, count: 6 },
    { entity: "post:low", recency: 4, count: 2 },
    { entity: "post:last", recency: 5, count: 1 },
  ];

  const ranked = rankPopularPosts(candidates);

  assert.deepEqual(
    ranked.map(({ entity }) => entity),
    [
      "post:tie-new",
      "post:tie-old",
      "post:newest",
      "post:middle",
      "post:low",
    ],
  );
  assert.equal(ranked.length, 5);
  assert.deepEqual(
    candidates.map(({ entity }) => entity),
    [
      "post:newest",
      "post:tie-new",
      "post:tie-old",
      "post:middle",
      "post:low",
      "post:last",
    ],
  );
});


test("loadPopularCounts makes one encoded count-only request per candidate", async () => {
  const candidates = [
    { entity: "post:one/with space", recency: 0 },
    { entity: "post:%already", recency: 1 },
  ];
  const requests = [];
  const fetchImpl = async (url, options) => {
    requests.push({ url, options });
    const entity = url.endsWith("post%3Aone%2Fwith%20space")
      ? "post:one/with space"
      : "post:%already";
    return jsonResponse({ entity, count: entity.includes("one") ? 3 : 8 });
  };

  const ranked = await loadPopularCounts({
    endpoint: "https://kudos.example.test///",
    candidates,
    fetchImpl,
  });

  assert.deepEqual(
    requests.map(({ url }) => url),
    [
      "https://kudos.example.test/post%3Aone%2Fwith%20space",
      "https://kudos.example.test/post%3A%25already",
    ],
  );
  assert.equal(requests.length, candidates.length);
  assert.equal(
    requests.some(({ url }) => new URL(url).pathname.endsWith("/kudos")),
    false,
  );
  const signals = requests.map(({ options }) => options.signal);
  assert.ok(signals.every((signal) => signal instanceof AbortSignal));
  assert.ok(signals.every((signal) => signal === signals[0]));
  for (const { options } of requests) {
    assert.equal(options.method, "GET");
    assert.equal(options.credentials, "omit");
    assert.equal(options.referrerPolicy, "no-referrer");
  }
  assert.deepEqual(
    ranked.map(({ entity, count }) => ({ entity, count })),
    [
      { entity: "post:%already", count: 8 },
      { entity: "post:one/with space", count: 3 },
    ],
  );
});


test("loadPopularCounts skips all requests for zero or one candidate", async () => {
  let calls = 0;
  const fetchImpl = async () => {
    calls += 1;
    throw new Error("must not fetch");
  };
  const empty = [];
  const single = [{ entity: "post:only", recency: 0 }];

  const emptyResult = await loadPopularCounts({
    endpoint: "https://kudos.example.test",
    candidates: empty,
    fetchImpl,
  });
  const singleResult = await loadPopularCounts({
    endpoint: "https://kudos.example.test",
    candidates: single,
    fetchImpl,
  });

  assert.equal(calls, 0);
  assert.deepEqual(emptyResult, empty);
  assert.deepEqual(singleResult, single);
  assert.notEqual(emptyResult, empty);
  assert.notEqual(singleResult, single);
});


test("loadPopularCounts rejects every malformed successful count payload", async (context) => {
  const invalidPayloads = [
    null,
    [],
    {},
    { entity: "post:wrong", count: 4 },
    { count: 4 },
    { entity: "post:target" },
    { entity: "post:target", count: -1 },
    { entity: "post:target", count: 1.5 },
    { entity: "post:target", count: Number.MAX_SAFE_INTEGER + 1 },
    { entity: "post:target", count: "4" },
  ];

  for (const payload of invalidPayloads) {
    await context.test(JSON.stringify(payload), async () => {
      const fetchImpl = async (url) => {
        const entity = url.endsWith("post%3Atarget")
          ? "post:target"
          : "post:sibling";
        return jsonResponse(entity === "post:target"
          ? payload
          : { entity, count: 1 });
      };

      await assert.rejects(loadPopularCounts({
        endpoint: "https://kudos.example.test",
        candidates: [
          { entity: "post:target", recency: 0 },
          { entity: "post:sibling", recency: 1 },
        ],
        fetchImpl,
      }));
    });
  }
});


test("loadPopularCounts rejects invalid JSON and non-2xx responses", async (context) => {
  const candidates = [
    { entity: "post:first", recency: 0 },
    { entity: "post:second", recency: 1 },
  ];

  await context.test("invalid JSON", async () => {
    await assert.rejects(loadPopularCounts({
      endpoint: "https://kudos.example.test",
      candidates,
      fetchImpl: async () => invalidJsonResponse(),
    }), /invalid JSON/i);
  });

  await context.test("non-2xx", async () => {
    await assert.rejects(loadPopularCounts({
      endpoint: "https://kudos.example.test",
      candidates,
      fetchImpl: async () => jsonResponse({
        entity: "post:first",
        count: 1,
      }, 503),
    }), /503/);
  });
});


test("loadPopularCounts uses one timeout to abort the full ranking", async () => {
  const signals = [];
  const fetchImpl = async (url, { signal }) => {
    signals.push(signal);
    return new Promise((resolve, reject) => {
      signal.addEventListener("abort", () => reject(signal.reason), {
        once: true,
      });
    });
  };

  await assert.rejects(loadPopularCounts({
    endpoint: "https://kudos.example.test",
    candidates: [
      { entity: "post:first", recency: 0 },
      { entity: "post:second", recency: 1 },
    ],
    fetchImpl,
    timeoutMs: 5,
  }), /timed out/i);

  assert.equal(signals.length, 2);
  assert.equal(signals[0], signals[1]);
  assert.equal(signals[0].aborted, true);
});


test("one failed count prevents a partial ranking", async () => {
  const candidates = [
    { entity: "post:valid", recency: 0 },
    { entity: "post:invalid", recency: 1 },
  ];
  const original = structuredClone(candidates);

  await assert.rejects(loadPopularCounts({
    endpoint: "https://kudos.example.test",
    candidates,
    fetchImpl: async (url) => jsonResponse(
      url.endsWith("post%3Avalid")
        ? { entity: "post:valid", count: 100 }
        : { entity: "post:invalid", count: -1 },
    ),
  }));

  assert.deepEqual(candidates, original);
});


test("the first failed count aborts a pending sibling", async () => {
  const pendingStarted = deferred();
  let pendingAborted = false;
  const fetchImpl = (url, { signal }) => {
    if (url.endsWith("post%3Afailure")) {
      return Promise.reject(new Error("first request failed"));
    }
    pendingStarted.resolve();
    return new Promise((resolve, reject) => {
      signal.addEventListener("abort", () => {
        pendingAborted = true;
        reject(signal.reason);
      }, { once: true });
    });
  };

  const loading = loadPopularCounts({
    endpoint: "https://kudos.example.test",
    candidates: [
      { entity: "post:failure", recency: 0 },
      { entity: "post:pending", recency: 1 },
    ],
    fetchImpl,
  });
  await pendingStarted.promise;

  await assert.rejects(loading, /first request failed/);
  assert.equal(pendingAborted, true);
});


test("mountPopularPosts reveals exactly five ranked candidates after success", async () => {
  const dom = popularDom(6);
  const counts = new Map([
    ["post:item-0", 4],
    ["post:item-1", 9],
    ["post:item-2", 9],
    ["post:item-3", 3],
    ["post:item-4", 2],
    ["post:item-5", 1],
  ]);
  const fetchImpl = async (url) => {
    const entity = decodeURIComponent(new URL(url).pathname.slice(1));
    return jsonResponse({ entity, count: counts.get(entity) });
  };

  const controller = mountPopularPosts(dom.root, fetchImpl, { error() {} });
  await controller.ready;

  assert.equal(dom.list.hidden, false);
  assert.deepEqual(
    dom.list.children.map(({ dataset }) => dataset.entity),
    [
      "post:item-1",
      "post:item-2",
      "post:item-0",
      "post:item-3",
      "post:item-4",
    ],
  );
  assert.equal(dom.list.children.length, 5);
  assert.equal(dom.rootAttributes.get("aria-busy"), "false");
  assert.equal(dom.root.dataset.popularState, "ready");
  assert.equal(dom.status.textContent, "Popular posts loaded");
  assert.deepEqual(dom.statusWrites, ["Popular posts loaded"]);
  assert.deepEqual(dom.removedStatusClasses, []);
});


test("mountPopularPosts contains failures and exposes one unavailable status", async () => {
  const dom = popularDom(2);
  const logged = [];
  const logger = {
    error(...args) {
      logged.push(args);
    },
  };
  const controller = mountPopularPosts(
    dom.root,
    async () => { throw new Error("offline"); },
    logger,
  );

  await assert.doesNotReject(controller.ready);

  assert.equal(dom.list.hidden, true);
  assert.equal(dom.rootAttributes.get("aria-busy"), "false");
  assert.equal(dom.root.dataset.popularState, "error");
  assert.equal(
    dom.status.textContent,
    "Popular posts are temporarily unavailable",
  );
  assert.deepEqual(
    dom.statusWrites,
    ["Popular posts are temporarily unavailable"],
  );
  assert.deepEqual(dom.removedStatusClasses, ["visually-hidden"]);
  assert.equal(logged.length, 1);
});
