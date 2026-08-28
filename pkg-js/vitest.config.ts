import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vitest/config";

// The example apps keep their own tests next to the app (examples/*/tests).
// They are included here on purpose: they mount each example's real www/ui.js
// against these hooks, so a change to the package that breaks an example fails
// the package's test run rather than being discovered later.
const repoRoot = path.resolve(__dirname, "..");

const dep = (id: string) => path.resolve(__dirname, "node_modules", id);

export default defineConfig({
  plugins: [react()],
  resolve: {
    // The example tests live outside pkg-js, so node resolution would not find
    // pkg-js/node_modules. Alias the few packages they need.
    alias: {
      "@testing-library/react": dep("@testing-library/react"),
      "react-dom/client": dep("react-dom/client.js"),
      "react-dom": dep("react-dom"),
      react: dep("react"),
    },
  },
  test: {
    environment: "jsdom",
    include: [
      "src/**/*.test.{ts,tsx}",
      "../examples/**/tests/*.test.{ts,tsx}",
    ],
  },
  server: {
    // The example tests and the harness live outside pkg-js.
    fs: { allow: [repoRoot] },
  },
});
