import { describe, expect, it } from "vitest";
import { installGlobal } from "../global";

/**
 * The `window.shinyreact` surface is a published API — downstream no-build apps
 * read hooks off it by name, and ESM builds externalize React to it. Nothing
 * asserted its shape, so the object literal in `global.ts` and the `Window`
 * interface beside it could drift together silently and still typecheck.
 */
describe("installGlobal", () => {
  it("installs exactly the documented public surface", () => {
    installGlobal();

    expect(Object.keys(window.shinyreact).sort()).toEqual([
      "ImageOutput",
      "MISSING",
      "React",
      "ReactDOM",
      "ShinyModuleProvider",
      "ShinyOutput",
      "ShinyReactComponentElement",
      "useSetShinyInput",
      "useShinyBusy",
      "useShinyInitialized",
      "useShinyInput",
      "useShinyInputValue",
      "useShinyMessageHandler",
      "useShinyOutputError",
      "useShinyOutputStatus",
      "useShinyOutputValue",
    ]);
  });

  it("exposes React and ReactDOM so downstream builds share one instance", () => {
    installGlobal();

    // Two Reacts on a page breaks hooks, so these must be the real modules
    // rather than re-exports of something else.
    expect(typeof window.shinyreact.React.createElement).toBe("function");
    expect(typeof window.shinyreact.ReactDOM.createRoot).toBe("function");
  });

  it("is idempotent — a second install replaces the namespace cleanly", () => {
    installGlobal();
    const first = window.shinyreact;
    installGlobal();

    expect(window.shinyreact).not.toBe(first);
    expect(Object.keys(window.shinyreact).sort()).toEqual(
      Object.keys(first).sort(),
    );
  });
});
