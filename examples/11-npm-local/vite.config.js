import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Nothing is externalized: React, ReactDOM and the `@posit/shinyreact` hooks
// are all bundled into www/ui.js. The server injects no JS of its own, so
// there is no `window.shinyreact` to borrow a React instance from — and no
// second copy of the runtime on the page either.
export default defineConfig({
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  plugins: [react()],
  build: {
    outDir: "www",
    emptyOutDir: false,
    cssCodeSplit: false,
    lib: {
      entry: path.resolve(__dirname, "src/ui.jsx"),
      formats: ["iife"],
      name: "NpmLocal",
      fileName: () => "ui.js",
    },
    rollupOptions: {
      // Name the emitted CSS asset ui.css (Vite 5 lib mode defaults to style.css).
      output: { assetFileNames: "ui.[ext]" },
    },
  },
});
