import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

import { shinyreactDevStub } from "./vite-dev-stub.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
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
  // No `resolve.dedupe` and no `server.fs.allow`: `@posit-dev/shinyreact` is an
  // ordinary registry dependency, so it is not symlinked, brings no nested
  // `node_modules`, and takes React from this app as a peer.
  server: {
    port: 5173,
    strictPort: true, // keep the stub's hard-coded :5173 honest
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
