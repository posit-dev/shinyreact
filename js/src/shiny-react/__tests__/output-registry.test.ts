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
    const dispose = registry.add("out1", vi.fn(), vi.fn(), vi.fn());
    expect(typeof dispose).toBe("function");
  });

  it("dispose removes only its own subscribers", () => {
    const registry = new OutputRegistry();
    const setVal1 = vi.fn();
    const setStatus1 = vi.fn();
    const setErr1 = vi.fn();
    const setVal2 = vi.fn();
    const setStatus2 = vi.fn();
    const setErr2 = vi.fn();

    const dispose1 = registry.add("out1", setVal1, setStatus1, setErr1);
    registry.add("out1", setVal2, setStatus2, setErr2);

    dispose1();

    const entry = registry.get("out1");
    expect(entry).toBeDefined();
    expect(entry!.isEmpty()).toBe(false);

    setStatus1.mockClear();
    setStatus2.mockClear();

    entry!.setValue("hello");
    expect(setVal1).not.toHaveBeenCalled();
    expect(setVal2).toHaveBeenCalledWith("hello");
    expect(setStatus1).not.toHaveBeenCalled();
    expect(setStatus2).toHaveBeenCalledWith("ready");

    entry!.setError({ message: "boom", call: [] });
    expect(setErr1).not.toHaveBeenCalled();
    expect(setErr2).toHaveBeenCalledWith({ message: "boom", call: [] });
  });

  it("scheduleCleanup removes entry and DOM when empty after RAF", async () => {
    const registry = new OutputRegistry();
    const dispose = registry.add("out1", vi.fn(), vi.fn(), vi.fn());
    expect(registry.has("out1")).toBe(true);
    expect(document.getElementById("out1")).not.toBeNull();

    dispose();

    expect(registry.has("out1")).toBe(true);
    await new Promise((resolve) => requestAnimationFrame(resolve));

    expect(registry.has("out1")).toBe(false);
    expect(document.getElementById("out1")).toBeNull();
  });

  it("scheduleCleanup preserves entry when re-subscribed before RAF", async () => {
    const registry = new OutputRegistry();
    const dispose1 = registry.add("out1", vi.fn(), vi.fn(), vi.fn());
    dispose1();

    const setVal2 = vi.fn();
    registry.add("out1", setVal2, vi.fn(), vi.fn());

    await new Promise((resolve) => requestAnimationFrame(resolve));

    expect(registry.has("out1")).toBe(true);
    const entry = registry.get("out1");
    entry!.setValue("preserved");
    expect(setVal2).toHaveBeenCalledWith("preserved");
  });

  it("add reuses existing entry and DOM element", () => {
    const registry = new OutputRegistry();
    registry.add("out1", vi.fn(), vi.fn(), vi.fn());
    const domBefore = document.getElementById("out1");

    registry.add("out1", vi.fn(), vi.fn(), vi.fn());
    const domAfter = document.getElementById("out1");

    expect(domBefore).toBe(domAfter);
  });

  it("add syncs new subscriber with current status on attach", () => {
    const registry = new OutputRegistry();
    // First subscriber attaches and bumps the entry to "ready" via setValue
    registry.add("out1", vi.fn(), vi.fn(), vi.fn());
    registry.get("out1")!.setValue("first");

    // Second subscriber should immediately receive the current status
    const setStatus2 = vi.fn();
    registry.add("out1", vi.fn(), setStatus2, vi.fn());
    expect(setStatus2).toHaveBeenCalledWith("ready");
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
