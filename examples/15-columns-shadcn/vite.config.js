import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// React/ReactDOM are externalized and pulled from window.shinyjson at runtime
// so this bundle shares the React instance that owns the shinyjson hooks.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  build: {
    outDir: "www",
    emptyOutDir: false,
    cssCodeSplit: false,
    lib: {
      entry: path.resolve(__dirname, "src/main.jsx"),
      formats: ["iife"],
      name: "ColumnsShadcn",
      fileName: () => "app.js",
    },
    rollupOptions: {
      external: ["react", "react-dom", "react-dom/client"],
      output: {
        globals: {
          react: "window.shinyjson.React",
          "react-dom": "window.shinyjson.ReactDOM",
          "react-dom/client": "window.shinyjson.ReactDOM",
        },
      },
    },
  },
});
