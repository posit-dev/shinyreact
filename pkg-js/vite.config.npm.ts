import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// The @posit/shinyreact npm build: ESM, React externalized as a peer
// dependency (so app bundlers resolve a single React — a dev build in dev
// mode). The IIFE build (vite.config.ts) inlines React instead; both are
// built from the same source. Type declarations come from tsconfig.npm.json.
export default defineConfig({
  build: {
    outDir: "dist-npm",
    emptyOutDir: true,
    sourcemap: true,
    lib: {
      entry: path.resolve(__dirname, "src/npm.ts"),
      formats: ["es"],
      fileName: () => "index.js",
    },
    rollupOptions: {
      external: ["react", "react-dom", "react-dom/client", "react/jsx-runtime"],
    },
  },
});
