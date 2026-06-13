import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  plugins: [react()],
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
      name: "ShinyMui",
      fileName: () => "mui.js",
    },
    rollupOptions: {
      // Same contract as shadcn: react and react-dom/client come from the host
      // (window.shinyreact), and "shinyreact" is the host hook module. react-dom
      // itself is NOT externalized — MUI's Modal/Popover/Select render through
      // portals (createPortal), which window.shinyreact.ReactDOM (react-dom/client)
      // does not expose. Emotion (MUI's styling engine) is bundled.
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
