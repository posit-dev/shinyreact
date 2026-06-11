import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// React/ReactDOM are externalized so this bundle shares the single React
// instance that owns the shinyreact hooks — two Reacts = broken hooks.
export default defineConfig({
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  build: {
    outDir: "../www",
    emptyOutDir: false,
    cssCodeSplit: false,
    lib: {
      entry: path.resolve(__dirname, "src/index.jsx"),
      formats: ["iife"],
      name: "ShinyShadcn",
      fileName: () => "shadcn.js",
    },
    rollupOptions: {
      // react-dom/client is externalized so our createRoot calls share the
      // same root as shinyreact. react-dom itself is NOT externalized because
      // window.shinyreact.ReactDOM only exposes react-dom/client (no createPortal).
      // Radix portals need createPortal, so we bundle that slice of react-dom;
      // it tree-shakes to ~2 kB and still uses the shared window.shinyreact.React.
      // The host page injects window.shinyreact at runtime — React, ReactDOM,
      // and the Shiny hooks all live on it. We externalize all three so this
      // bundle shares the host's single instances instead of bundling copies.
      // Importing from "shinyreact" compiles to property access on the global.
      external: ["react", "react-dom/client", "shinyreact"],
      output: {
        globals: {
          react: "window.shinyreact.React",
          "react-dom/client": "window.shinyreact.ReactDOM",
          shinyreact: "window.shinyreact",
        },
      },
    },
  },
});
