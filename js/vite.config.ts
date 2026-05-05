import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  build: {
    lib: {
      entry: "src/index.ts",
      name: "shinyreact",
      formats: ["iife"],
      fileName: () => "shinyreact.js",
    },
    outDir: "dist",
    rollupOptions: {
      // Bundle everything including React — no externals
      output: {
        assetFileNames: "shinyreact.[ext]",
      },
    },
  },
});
