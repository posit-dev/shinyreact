import { afterEach, describe, expect, it, vi } from "vitest";

// Mock getShiny — OutputRegistry constructor accesses document.body
vi.mock("../get-shiny", () => ({
  getShiny: vi.fn(() => undefined),
}));

import {
  OutputRegistry,
  OutputRegistryEntry,
  type OutputStatus,
  type ErrorsMessageValue,
} from "../output-registry";

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

describe("OutputRegistryEntry status lifecycle", () => {
  it("starts in pending status", () => {
    const entry = new OutputRegistryEntry("test");
    expect(entry.getStatus()).toBe("pending");
  });

  it("setValue moves status to ready and fans out to subscribers", () => {
    const entry = new OutputRegistryEntry("test");
    const setVal = vi.fn();
    const setStatus = vi.fn();
    entry.addUseStateSetValueFn(setVal);
    entry.addUseStateSetStatusFn(setStatus);

    entry.setValue("hello");

    expect(entry.getStatus()).toBe("ready");
    expect(setVal).toHaveBeenCalledWith("hello");
    expect(setStatus).toHaveBeenCalledWith("ready");
  });

  it("setRecalculating(true) on a ready entry transitions to recalculating", () => {
    const entry = new OutputRegistryEntry("test");
    entry.setValue("x");
    const setStatus = vi.fn();
    entry.addUseStateSetStatusFn(setStatus);

    entry.setRecalculating(true);

    expect(entry.getStatus()).toBe("recalculating");
    expect(setStatus).toHaveBeenLastCalledWith("recalculating");
  });

  it("setRecalculating(false) after recalculating returns to ready", () => {
    const entry = new OutputRegistryEntry("test");
    entry.setValue("x");
    entry.setRecalculating(true);
    const setStatus = vi.fn();
    entry.addUseStateSetStatusFn(setStatus);

    entry.setRecalculating(false);

    expect(entry.getStatus()).toBe("ready");
    expect(setStatus).toHaveBeenLastCalledWith("ready");
  });

  it("setRecalculating(true) before any value keeps status pending", () => {
    const entry = new OutputRegistryEntry("test");
    const setStatus = vi.fn();
    entry.addUseStateSetStatusFn(setStatus);

    entry.setRecalculating(true);

    // Server is recalculating but we have never received a value — UI
    // should still be in the pending/skeleton state, not show stale "ready".
    expect(entry.getStatus()).toBe("pending");
  });

  it("setError moves status to error and fans out error", () => {
    const entry = new OutputRegistryEntry("test");
    const setStatus = vi.fn();
    const setError = vi.fn();
    entry.addUseStateSetStatusFn(setStatus);
    entry.addUseStateSetErrorFn(setError);

    const err: ErrorsMessageValue = { message: "boom", call: [] };
    entry.setError(err);

    expect(entry.getStatus()).toBe("error");
    expect(setStatus).toHaveBeenLastCalledWith("error");
    expect(setError).toHaveBeenCalledWith(err);
  });

  it("setValue after setError clears the error and returns to ready", () => {
    const entry = new OutputRegistryEntry("test");
    entry.setError({ message: "boom", call: [] });
    const setError = vi.fn();
    entry.addUseStateSetErrorFn(setError);

    entry.setValue("recovered");

    expect(entry.getStatus()).toBe("ready");
    expect(setError).toHaveBeenLastCalledWith(null);
  });

  it("isEmpty considers status and error subscribers", () => {
    const entry = new OutputRegistryEntry("test");
    expect(entry.isEmpty()).toBe(true);
    const fn = vi.fn();
    entry.addUseStateSetStatusFn(fn);
    expect(entry.isEmpty()).toBe(false);
    entry.removeUseStateSetStatusFn(fn);
    expect(entry.isEmpty()).toBe(true);
  });
});

const _checkStatusType: OutputStatus[] = [
  "pending",
  "ready",
  "recalculating",
  "error",
];
void _checkStatusType;
