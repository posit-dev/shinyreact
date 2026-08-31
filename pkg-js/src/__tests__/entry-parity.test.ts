/* eslint-disable @typescript-eslint/no-explicit-any */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/**
 * The two entry points must install the same client behavior.
 *
 * This exists because they silently diverged once: `installDepDiscovery()` was
 * called from `index.ts` (IIFE) and not from `npm.ts`, so bundler-tier apps got
 * no renderer dependency discovery and never sent the `.shinyreact_init` ping
 * that bootstraps it server-side — a `<ShinyOutput>` whose binding arrived late
 * just never bound, with no error (posit-dev/shinyreact#233).
 *
 * Nothing caught it because nothing asserted what an entry point *does*. These
 * tests import each entry for real and check the observable side effects, so
 * the next divergence fails here instead of in someone's app.
 */

function fakeShiny() {
  return {
    addCustomMessageHandler: vi.fn(),
    setInputValue: vi.fn(),
    initializedPromise: Promise.resolve(),
    bindAll: vi.fn(),
    unbindAll: vi.fn(),
    outputBindings: { register: vi.fn() },
    OutputBinding: class {},
  };
}

beforeEach(() => {
  vi.resetModules();
  (window as any).Shiny = fakeShiny();
  // `installGlobal()` leaves `window.shinyreact` behind, and resetModules()
  // does not undo DOM writes. Without this, whether a test sees the global
  // depends on which tests ran before it.
  delete (window as any).shinyreact;
});

afterEach(() => {
  delete (window as any).Shiny;
  delete (window as any).shinyreact;
});

describe("entry point parity", () => {
  it("the IIFE entry installs dependency discovery", async () => {
    await import("../index");

    expect((window as any).Shiny.addCustomMessageHandler).toHaveBeenCalledWith(
      "shinyreact-deps",
      expect.any(Function),
    );
  });

  it("the npm entry installs dependency discovery too (#233)", async () => {
    await import("../npm");

    expect((window as any).Shiny.addCustomMessageHandler).toHaveBeenCalledWith(
      "shinyreact-deps",
      expect.any(Function),
    );
  });

  it("both entries send the .shinyreact_init bootstrap ping", async () => {
    await import("../npm");
    await vi.waitFor(() =>
      expect((window as any).Shiny.setInputValue).toHaveBeenCalledWith(
        ".shinyreact_init:shinyreact.init",
        1,
      ),
    );

    vi.resetModules();
    (window as any).Shiny = fakeShiny();
    await import("../index");
    await vi.waitFor(() =>
      expect((window as any).Shiny.setInputValue).toHaveBeenCalledWith(
        ".shinyreact_init:shinyreact.init",
        1,
      ),
    );
  });

  it("only the npm entry treats a missing config tag as fatal", async () => {
    // The other deliberate tier difference. Asserted at the *entry* level:
    // use-shiny-restore.test.tsx pins the strict behavior by calling
    // requireShinyReactConfigTag() directly, which would still pass if
    // npm.ts stopped opting in.
    await import("../npm");
    const { isShinyReactConfigTagRequired } = await import(
      "../shiny-react/config"
    );
    expect(isShinyReactConfigTagRequired()).toBe(true);

    vi.resetModules();
    (window as any).Shiny = fakeShiny();
    await import("../index");
    const iife = await import("../shiny-react/config");
    expect(iife.isShinyReactConfigTagRequired()).toBe(false);
  });

  it("only the IIFE entry installs the window.shinyreact global", async () => {
    // Deliberate divergence, not drift: npm consumers import the hooks
    // directly, and the global exists so no-build pages can read them off
    // `window`. Pinned so flipping it is a decision.
    await import("../npm");
    expect((window as any).shinyreact).toBeUndefined();

    vi.resetModules();
    await import("../index");
    expect((window as any).shinyreact).toBeDefined();
  });

  it("the npm entry warns when the IIFE bundle is on the page too", async () => {
    // The double-load case: an npm-tier app whose page left shinyreact_js at
    // its default of "server". Harmless but wasteful, and silent until now —
    // the warning is the only thing that says to pass shinyreact_js="client".
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    await import("../index"); // the IIFE, as the server would inject it
    vi.resetModules(); // a *separate* copy of the library, as on a real page
    await import("../npm");

    expect(warn).toHaveBeenCalledOnce();
    expect(warn.mock.calls[0]?.[0]).toMatch(/shinyreact_js="client"/);
    warn.mockRestore();
  });

  it("the npm entry is silent when it is the only runtime", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    await import("../npm");

    expect(warn).not.toHaveBeenCalled();
    warn.mockRestore();
  });
});
