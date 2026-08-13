import assert from "node:assert/strict";
import { test } from "node:test";

import { makeDevStub } from "../vite-dev-stub.js";

test("stub installs the Fast Refresh preamble before importing the entry", () => {
  const out = makeDevStub("http://localhost:5173", "src/ui.tsx");

  const refreshIdx = out.indexOf("@react-refresh");
  const clientIdx = out.indexOf("@vite/client");
  const entryIdx = out.indexOf("src/ui.tsx");

  assert.ok(refreshIdx >= 0, "imports @react-refresh");
  assert.match(out, /injectIntoGlobalHook/, "calls injectIntoGlobalHook");
  assert.match(out, /__vite_plugin_react_preamble_installed__/, "sets preamble flag");
  assert.ok(refreshIdx < clientIdx, "refresh preamble comes before @vite/client");
  assert.ok(clientIdx < entryIdx, "@vite/client comes before the entry");
  assert.match(
    out,
    /await import\("http:\/\/localhost:5173\/src\/ui\.tsx"\)/,
    "entry is loaded via dynamic import (so the preamble runs first)",
  );
});

test("stub honors a non-default origin", () => {
  const out = makeDevStub("http://localhost:5199", "src/ui.tsx");
  assert.match(out, /localhost:5199\/@vite\/client/);
  assert.match(out, /localhost:5199\/src\/ui\.tsx/);
});

test("stub strips a trailing slash from origin", () => {
  const out = makeDevStub("http://localhost:5173/", "src/ui.tsx");
  assert.ok(!out.includes("//@vite/client"), "no double slash before @vite/client");
  assert.ok(!out.includes("//@react-refresh"), "no double slash before @react-refresh");
  assert.match(out, /http:\/\/localhost:5173\/@vite\/client/);
});
