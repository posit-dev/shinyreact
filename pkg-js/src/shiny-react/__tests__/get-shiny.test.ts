/* eslint-disable @typescript-eslint/no-explicit-any */
import { afterEach, describe, expect, it, vi } from "vitest";

import { getShiny } from "../get-shiny";

afterEach(() => {
  vi.unstubAllGlobals();
  delete (window as any).Shiny;
});

describe("getShiny", () => {
  it("returns window.Shiny when Shiny is present", () => {
    const shiny = { setInputValue: vi.fn() };
    (window as any).Shiny = shiny;

    expect(getShiny()).toBe(shiny);
  });

  it("returns undefined when Shiny has not loaded yet", () => {
    expect(getShiny()).toBeUndefined();
  });

  it("returns undefined instead of throwing when there is no window", () => {
    // A debounced input write can fire after the document is gone — a jsdom
    // test tearing down, or a page unloading. Reading the bare `window`
    // identifier there is a ReferenceError, which surfaces as an unhandled
    // error and fails the whole run even though every test passed.
    vi.stubGlobal("window", undefined);

    expect(() => getShiny()).not.toThrow();
    expect(getShiny()).toBeUndefined();
  });
});
