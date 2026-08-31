import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

import { shinyreactDevStub } from "./vite-dev-stub.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// examples/09-hmr -> repo root (two levels up).
const repoRoot = path.resolve(__dirname, "../..");
const ENTRY = "src/ui.tsx";

export default defineConfig(({ command }) => ({
  define: {
    "process.env.NODE_ENV": JSON.stringify(command === "build" ? "production" : "development"),
  },
  plugins: [
    react(),
    // serve only: writes www/ui.js as the dev stub (apply:"serve" inside).
    shinyreactDevStub({ entry: ENTRY, outFile: "www/ui.js" }),
  ],
  resolve: {
    // `@posit/shinyreact` is a `file:` dep, so it is symlinked and brings its
    // own node_modules. Without dedupe, App.tsx and the hooks would each get a
    // React copy and every hook call would throw.
    dedupe: ["react", "react-dom"],
  },
  server: {
    port: 5173,
    strictPort: true, // keep the stub's hard-coded :5173 honest
    // `@posit/shinyreact` resolves through a symlink to the repo's pkg-js/.
    fs: { allow: [repoRoot] },
  },
  build: {
    outDir: "www",
    emptyOutDir: false,
    lib: {
      entry: path.resolve(__dirname, ENTRY),
      formats: ["iife"],
      name: "HmrExample",
      fileName: () => "ui.js",
    },
    // No externals: this app bundles its own React, in both modes. That is the
    // point of the npm tier -- a development React with Fast Refresh in dev.
  },
}));
