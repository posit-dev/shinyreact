import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vitest/config";

// Lets the example apps' UI tests run from the examples tree, without
// installing the shinyreact packages:
//
//   npm install         # once
//   npm test            # every example
//   npx vitest run 01-hello
//
// From inside a single app: `npx vitest run --root .. 01-hello`.
//
// pkg-js runs these same files from its own config, so a package change that
// breaks an example fails there too. The two configs must agree; they are
// short on purpose.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["*/tests/*.test.{ts,tsx}"],
  },
  server: {
    // examples/testing/mount.ts imports the package source from pkg-js/src.
    fs: { allow: [path.resolve(__dirname, "..")] },
  },
});
