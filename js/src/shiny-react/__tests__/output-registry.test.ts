import { afterEach, describe, expect, it, vi } from "vitest";

// Mock getShiny — OutputRegistry constructor accesses document.body
vi.mock("../get-shiny", () => ({
  getShiny: vi.fn(() => undefined),
}));

import { OutputRegistry, OutputRegistryEntry } from "../output-registry";

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

describe("OutputRegistry", () => {
  afterEach(() => {
    // Clean up any containers added to document.body
    document
      .querySelectorAll(".shiny-react-output-container")
      .forEach((el) => el.remove());
  });

  it("add returns a dispose function", () => {
    const registry = new OutputRegistry();
    const dispose = registry.add("out1", vi.fn(), vi.fn());
    expect(typeof dispose).toBe("function");
  });

  it("dispose removes only its own subscribers", () => {
    const registry = new OutputRegistry();
    const setVal1 = vi.fn();
    const setRecalc1 = vi.fn();
    const setVal2 = vi.fn();
    const setRecalc2 = vi.fn();

    const dispose1 = registry.add("out1", setVal1, setRecalc1);
    registry.add("out1", setVal2, setRecalc2);

    dispose1();

    // Entry should still exist because subscriber 2 is still there
    const entry = registry.get("out1");
    expect(entry).toBeDefined();
    expect(entry!.isEmpty()).toBe(false);

    // Only subscriber 2 should receive values
    entry!.setValue("hello");
    expect(setVal1).not.toHaveBeenCalled();
    expect(setVal2).toHaveBeenCalledWith("hello");
  });

  it("scheduleCleanup removes entry and DOM when empty after RAF", async () => {
    const registry = new OutputRegistry();
    const dispose = registry.add("out1", vi.fn(), vi.fn());
    expect(registry.has("out1")).toBe(true);
    expect(document.getElementById("out1")).not.toBeNull();

    dispose();

    // Entry still exists synchronously (RAF hasn't fired)
    expect(registry.has("out1")).toBe(true);

    // Wait for RAF to fire
    await new Promise((resolve) => requestAnimationFrame(resolve));

    // Now the entry and DOM element should be cleaned up
    expect(registry.has("out1")).toBe(false);
    expect(document.getElementById("out1")).toBeNull();
  });

  it("scheduleCleanup preserves entry when re-subscribed before RAF", async () => {
    const registry = new OutputRegistry();
    const dispose1 = registry.add("out1", vi.fn(), vi.fn());

    dispose1();

    // Simulate remount — new subscriber added before RAF fires
    const setVal2 = vi.fn();
    registry.add("out1", setVal2, vi.fn());

    // Wait for RAF
    await new Promise((resolve) => requestAnimationFrame(resolve));

    // Entry should still exist — new subscriber saved it
    expect(registry.has("out1")).toBe(true);
    const entry = registry.get("out1");
    entry!.setValue("preserved");
    expect(setVal2).toHaveBeenCalledWith("preserved");
  });

  it("add reuses existing entry and DOM element", () => {
    const registry = new OutputRegistry();
    registry.add("out1", vi.fn(), vi.fn());
    const domBefore = document.getElementById("out1");

    registry.add("out1", vi.fn(), vi.fn());
    const domAfter = document.getElementById("out1");

    // Same DOM element, not a duplicate
    expect(domBefore).toBe(domAfter);
  });
});
