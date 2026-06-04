import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

import { shinyreactDevStub } from "./vite-dev-stub.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// examples/ui-tsx/09-hmr -> repo root (three levels up).
const repoRoot = path.resolve(__dirname, "../../..");
const ENTRY = "src/ui.tsx";

export default defineConfig(({ command }) => ({
  define: {
    "process.env.NODE_ENV": JSON.stringify(command === "build" ? "production" : "development"),
  },
  plugins: [
    react(),
    // serve only: writes www/app.js as the dev stub (apply:"serve" inside).
    shinyreactDevStub({ entry: ENTRY, outFile: "www/app.js" }),
  ],
  resolve: {
    // One React instance across App.tsx and the bundled shiny-react source.
    dedupe: ["react", "react-dom"],
    alias: {
      "shiny-bridge": path.resolve(
        __dirname,
        command === "serve" ? "src/shiny-bridge.dev.ts" : "src/shiny-bridge.prod.ts",
      ),
    },
  },
  server: {
    port: 5173,
    strictPort: true, // keep the stub's hard-coded :5173 honest
    // Allow serving the vendored shiny-react source that lives outside this dir.
    fs: { allow: [repoRoot] },
  },
  build: {
    outDir: "www",
    emptyOutDir: false,
    lib: {
      entry: path.resolve(__dirname, ENTRY),
      formats: ["iife"],
      name: "HmrExample",
      fileName: () => "app.js",
    },
    rollupOptions: {
      external: ["react", "react-dom", "react-dom/client"],
      output: {
        globals: {
          react: "window.shinyreact.React",
          "react-dom": "window.shinyreact.ReactDOM",
          "react-dom/client": "window.shinyreact.ReactDOM",
        },
      },
    },
  },
}));
