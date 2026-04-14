import { describe, expect, it, vi } from "vitest";

// Mock getShiny — OutputRegistry constructor accesses document.body
vi.mock("../get-shiny", () => ({
  getShiny: vi.fn(() => undefined),
}));

import { OutputRegistryEntry } from "../output-registry";

describe("OutputRegistryEntry", () => {
  it("isEmpty returns true on fresh entry", () => {
    const entry = new OutputRegistryEntry("test");
    expect(entry.isEmpty()).toBe(true);
  });

  it("isEmpty returns false after adding setValue subscriber", () => {
    const entry = new OutputRegistryEntry("test");
    entry.addUseStateSetValueFn(vi.fn());
    expect(entry.isEmpty()).toBe(false);
  });

  it("isEmpty returns false after adding setRecalculating subscriber", () => {
    const entry = new OutputRegistryEntry("test");
    entry.addUseStateSetRecalculatingFn(vi.fn());
    expect(entry.isEmpty()).toBe(false);
  });

  it("isEmpty returns true after removing all subscribers", () => {
    const entry = new OutputRegistryEntry("test");
    const setVal = vi.fn();
    const setRecalc = vi.fn();
    entry.addUseStateSetValueFn(setVal);
    entry.addUseStateSetRecalculatingFn(setRecalc);

    entry.removeUseStateSetValueFn(setVal);
    entry.removeUseStateSetRecalculatingFn(setRecalc);
    expect(entry.isEmpty()).toBe(true);
  });
});
