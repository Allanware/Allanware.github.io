import assert from "node:assert/strict";
import { createServer } from "node:http";
import test from "node:test";

import {
  createKudosClient,
  mountKudos,
  renderKudos,
} from "../assets/js/kudos.mjs";


// API contract: puinoib/kudos v0.2.0 at
// b449185be66d239555bf1242fec1169a0a09517f.
// Node's HTTP client does not enforce browser CORS; that remains a browser or
// post-deployment check.


function listen(server) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve(server.address()));
  });
}


function close(server) {
  return new Promise((resolve, reject) => {
    server.close((error) => error ? reject(error) : resolve());
  });
}


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


function kudosDom() {
  const attributes = new Map();
  const listeners = new Map();
  const button = {
    disabled: false,
    classList: {
      toggle: (name, value) => attributes.set(`class:${name}`, value),
    },
    setAttribute: (name, value) => attributes.set(name, value),
    removeAttribute: (name) => attributes.delete(name),
    addEventListener: (name, handler) => listeners.set(name, handler),
  };
  const count = { textContent: "—" };
  const status = { textContent: "Loading" };
  const root = {
    hidden: true,
    dataset: {
      addLabel: "Upvote",
      removeLabel: "Remove upvote",
      unavailableLabel: "Unavailable",
      updateFailedLabel: "Try again",
      kudosEndpoint: "https://kudos.example.test",
      kudosEntity: "post:shared-article",
      kudosState: "loading",
    },
    setAttribute: (name, value) => attributes.set(`root:${name}`, value),
    querySelector: (selector) => ({
      "[data-kudos-button]": button,
      "[data-kudos-count]": count,
      "[data-kudos-status]": status,
    })[selector],
  };
  return {
    root,
    button,
    count,
    status,
    attributes,
    click: () => listeners.get("click")(),
  };
}


test("Kudos rendering updates the exact count and boolean voter state", () => {
  const dom = kudosDom();
  renderKudos(dom.root, { count: 8, hasKudos: true });

  assert.equal(dom.count.textContent, "8");
  assert.equal(dom.status.textContent, "");
  assert.equal(dom.attributes.get("aria-pressed"), "true");
  assert.equal(dom.attributes.get("aria-label"), "Remove upvote");
  assert.equal(dom.attributes.get("class:upvoted"), true);
  assert.equal(dom.attributes.get("root:aria-busy"), "false");
  assert.equal(dom.root.dataset.kudosState, "ready");
});


test("Kudos ignores clicks until both initial voter responses are valid", async () => {
  const dom = kudosDom();
  const pending = [];
  const methods = [];
  const fetchImpl = (url, options) => {
    methods.push(options?.method ?? "GET");
    return new Promise((resolve) => pending.push([url, resolve]));
  };

  const controller = mountKudos(dom.root, fetchImpl, { error() {} });
  assert.equal(dom.root.hidden, false);
  assert.equal(dom.button.disabled, true);
  assert.equal(dom.attributes.get("root:aria-busy"), "true");
  await dom.click();
  assert.deepEqual(methods, ["GET", "GET"]);

  pending[0][1](jsonResponse({
    entity: "post:shared-article",
    count: 7,
  }));
  pending[1][1](jsonResponse({
    entity: "post:shared-article",
    hasKudos: true,
  }));
  await controller.ready;
  assert.equal(dom.button.disabled, false);
  assert.equal(dom.attributes.get("aria-pressed"), "true");
  assert.equal(dom.root.dataset.kudosState, "ready");
});


test("Kudos takes a synchronous write lock and coalesces rapid clicks", async () => {
  const dom = kudosDom();
  const mutation = deferred();
  const methods = [];
  const fetchImpl = (url, options) => {
    const method = options?.method ?? "GET";
    methods.push(method);
    if (methods.length === 1) {
      return Promise.resolve(jsonResponse({
        entity: "post:shared-article",
        count: 7,
      }));
    }
    if (methods.length === 2) {
      return Promise.resolve(jsonResponse({
        entity: "post:shared-article",
        hasKudos: false,
      }));
    }
    return mutation.promise;
  };
  const controller = mountKudos(dom.root, fetchImpl, { error() {} });
  await controller.ready;

  const first = dom.click();
  assert.equal(dom.button.disabled, true);
  assert.equal(dom.root.dataset.kudosState, "writing");
  assert.equal(dom.attributes.get("root:aria-busy"), "true");
  await dom.click();
  assert.deepEqual(methods, ["GET", "GET", "POST"]);

  mutation.resolve(jsonResponse({
    entity: "post:shared-article",
    count: 8,
    hasKudos: true,
    changed: true,
  }));
  await first;
  assert.equal(dom.count.textContent, "8");
  assert.equal(dom.attributes.get("aria-pressed"), "true");
  assert.equal(dom.button.disabled, false);
});


test("Kudos load failure stays unavailable without exposing a false zero", async () => {
  const dom = kudosDom();
  const controller = mountKudos(
    dom.root,
    async () => { throw new Error("offline"); },
    { error() {} },
  );

  await controller.ready;
  assert.equal(dom.count.textContent, "—");
  assert.equal(dom.status.textContent, "Unavailable");
  assert.equal(dom.button.disabled, true);
  assert.equal(dom.attributes.has("aria-pressed"), false);
  assert.equal(dom.attributes.get("aria-label"), "Unavailable");
  assert.equal(dom.attributes.get("root:aria-busy"), "false");
  assert.equal(dom.root.dataset.kudosState, "error");
});


test("Kudos mutation failure preserves the last good state and permits retry", async () => {
  const dom = kudosDom();
  let mutationAttempts = 0;
  const fetchImpl = async (url, options) => {
    if (!options?.method && url.endsWith("/kudos")) {
      return jsonResponse({
        entity: "post:shared-article",
        hasKudos: false,
      });
    }
    if (!options?.method) {
      return jsonResponse({
        entity: "post:shared-article",
        count: 7,
      });
    }
    mutationAttempts += 1;
    if (mutationAttempts === 1) throw new Error("write failed");
    return jsonResponse({
      entity: "post:shared-article",
      count: 8,
      hasKudos: true,
      changed: true,
    });
  };
  const controller = mountKudos(dom.root, fetchImpl, { error() {} });
  await controller.ready;

  await dom.click();
  assert.equal(dom.count.textContent, "7");
  assert.equal(dom.attributes.get("aria-pressed"), "false");
  assert.equal(dom.attributes.get("aria-label"), "Upvote");
  assert.equal(dom.attributes.get("class:upvoted"), false);
  assert.equal(dom.status.textContent, "Try again");
  assert.equal(dom.button.disabled, false);
  assert.equal(dom.root.dataset.kudosState, "error");

  await dom.click();
  assert.equal(mutationAttempts, 2);
  assert.equal(dom.count.textContent, "8");
  assert.equal(dom.attributes.get("aria-pressed"), "true");
  assert.equal(dom.status.textContent, "");
});


test("Kudos rejects every malformed successful load payload", async (context) => {
  const invalidCountPayloads = [
    {},
    { entity: "post:other", count: 7 },
    { entity: "post:shared-article" },
    { entity: "post:shared-article", count: -1 },
    { entity: "post:shared-article", count: 1.5 },
    { entity: "post:shared-article", count: Number.MAX_SAFE_INTEGER + 1 },
    { entity: "post:shared-article", count: "7" },
  ];
  const invalidStatePayloads = [
    {},
    { entity: "post:other", hasKudos: false },
    { entity: "post:shared-article" },
    { entity: "post:shared-article", hasKudos: 0 },
    { entity: "post:shared-article", hasKudos: "false" },
  ];

  for (const [kind, payload] of [
    ...invalidCountPayloads.map((value) => ["count", value]),
    ...invalidStatePayloads.map((value) => ["state", value]),
  ]) {
    await context.test(`${kind}: ${JSON.stringify(payload)}`, async () => {
      const dom = kudosDom();
      const fetchImpl = async (url) => {
        if (url.endsWith("/kudos")) {
          return jsonResponse(kind === "state" ? payload : {
            entity: "post:shared-article",
            hasKudos: false,
          });
        }
        return jsonResponse(kind === "count" ? payload : {
          entity: "post:shared-article",
          count: 7,
        });
      };
      const controller = mountKudos(dom.root, fetchImpl, { error() {} });
      await controller.ready;
      assert.equal(dom.root.dataset.kudosState, "error");
      assert.equal(dom.count.textContent, "—");
      assert.equal(dom.attributes.has("aria-pressed"), false);
    });
  }

  await context.test("invalid JSON", async () => {
    const dom = kudosDom();
    const controller = mountKudos(
      dom.root,
      async () => invalidJsonResponse(),
      { error() {} },
    );
    await controller.ready;
    assert.equal(dom.root.dataset.kudosState, "error");
  });

  await context.test("non-2xx", async () => {
    const dom = kudosDom();
    const controller = mountKudos(
      dom.root,
      async () => jsonResponse({ error: "nope" }, 503),
      { error() {} },
    );
    await controller.ready;
    assert.equal(dom.root.dataset.kudosState, "error");
  });
});


test("Kudos rejects malformed mutation payloads without changing good state", async (context) => {
  const invalidPayloads = [
    {},
    { entity: "post:other", count: 8, hasKudos: true },
    { entity: "post:shared-article", count: -1, hasKudos: true },
    { entity: "post:shared-article", count: 8.5, hasKudos: true },
    { entity: "post:shared-article", count: Number.MAX_SAFE_INTEGER + 1, hasKudos: true },
    { entity: "post:shared-article", count: 8, hasKudos: 1 },
    { entity: "post:shared-article", count: "8", hasKudos: true },
  ];

  for (const payload of invalidPayloads) {
    await context.test(JSON.stringify(payload), async () => {
      const dom = kudosDom();
      const fetchImpl = async (url, options) => {
        if (options?.method) return jsonResponse(payload);
        if (url.endsWith("/kudos")) {
          return jsonResponse({
            entity: "post:shared-article",
            hasKudos: false,
          });
        }
        return jsonResponse({
          entity: "post:shared-article",
          count: 7,
        });
      };
      const controller = mountKudos(dom.root, fetchImpl, { error() {} });
      await controller.ready;
      await dom.click();
      assert.equal(dom.count.textContent, "7");
      assert.equal(dom.attributes.get("aria-pressed"), "false");
      assert.equal(dom.status.textContent, "Try again");
      assert.equal(dom.button.disabled, false);
    });
  }

  await context.test("invalid JSON", async () => {
    const dom = kudosDom();
    const fetchImpl = async (url, options) => {
      if (options?.method) return invalidJsonResponse();
      if (url.endsWith("/kudos")) {
        return jsonResponse({
          entity: "post:shared-article",
          hasKudos: false,
        });
      }
      return jsonResponse({ entity: "post:shared-article", count: 7 });
    };
    const controller = mountKudos(dom.root, fetchImpl, { error() {} });
    await controller.ready;
    await dom.click();
    assert.equal(dom.count.textContent, "7");
    assert.equal(dom.status.textContent, "Try again");
  });

  await context.test("non-2xx", async () => {
    const dom = kudosDom();
    const fetchImpl = async (url, options) => {
      if (options?.method) return jsonResponse({ error: "nope" }, 409);
      if (url.endsWith("/kudos")) {
        return jsonResponse({
          entity: "post:shared-article",
          hasKudos: false,
        });
      }
      return jsonResponse({ entity: "post:shared-article", count: 7 });
    };
    const controller = mountKudos(dom.root, fetchImpl, { error() {} });
    await controller.ready;
    await dom.click();
    assert.equal(dom.count.textContent, "7");
    assert.equal(dom.status.textContent, "Try again");
  });
});


test("Kudos uses one encoded entity and one slash for every API route", async () => {
  const requests = [];
  let count = 7;
  let hasKudos = false;
  const entityPath = "/post%3Ashared-article";
  const server = createServer((request, response) => {
    requests.push([request.method, request.url]);
    response.setHeader("content-type", "application/json");
    response.setHeader("access-control-allow-origin", "*");
    if (request.method === "GET" && request.url === entityPath) {
      response.end(JSON.stringify({
        entity: "post:shared-article",
        count,
      }));
      return;
    }
    if (request.url === `${entityPath}/kudos` && request.method === "GET") {
      response.end(JSON.stringify({
        entity: "post:shared-article",
        hasKudos,
      }));
      return;
    }
    if (request.url === `${entityPath}/kudos` && request.method === "POST") {
      hasKudos = true;
      count += 1;
      response.end(JSON.stringify({
        entity: "post:shared-article",
        count,
        hasKudos,
        changed: true,
      }));
      return;
    }
    if (request.url === `${entityPath}/kudos` && request.method === "DELETE") {
      hasKudos = false;
      count -= 1;
      response.end(JSON.stringify({
        entity: "post:shared-article",
        count,
        hasKudos,
        changed: true,
      }));
      return;
    }
    response.statusCode = 404;
    response.end(JSON.stringify({ error: "unexpected route" }));
  });

  const address = await listen(server);
  try {
    const client = createKudosClient({
      baseUrl: `http://127.0.0.1:${address.port}/`,
      entity: "post:shared-article",
      fetchImpl: fetch,
    });
    assert.deepEqual(await client.load(), { count: 7, hasKudos: false });
    assert.deepEqual(await client.toggle(false), { count: 8, hasKudos: true });
    assert.deepEqual(await client.toggle(true), { count: 7, hasKudos: false });
    assert.deepEqual(requests, [
      ["GET", entityPath],
      ["GET", `${entityPath}/kudos`],
      ["POST", `${entityPath}/kudos`],
      ["DELETE", `${entityPath}/kudos`],
    ]);
  } finally {
    await close(server);
  }
});
