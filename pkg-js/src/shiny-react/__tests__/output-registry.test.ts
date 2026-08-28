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

  it("manufactures a bare div — no debug text shipped into the page", () => {
    const registry = new OutputRegistry();
    registry.add("out1", vi.fn(), vi.fn(), vi.fn());

    const div = document.querySelector(
      ".shiny-react-output-container #out1",
    ) as HTMLElement;
    expect(div).not.toBeNull();
    expect(div.textContent).toBe("");
  });

  it("does not touch document until the first add()", () => {
    // Constructing the registry is part of shinyreact's one-time init, which a
    // DOM-less environment reaches; creating the container eagerly threw there.
    const before = document.querySelectorAll(
      ".shiny-react-output-container",
    ).length;
    new OutputRegistry();
    expect(
      document.querySelectorAll(".shiny-react-output-container").length,
    ).toBe(before);
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

  it("cleanup removes its own div, not a same-id element in the app's markup", async () => {
    // Output ids are author-chosen, so an app can legitimately have an element
    // with the same id. A document-global getElementById() would find that one
    // first and delete the app's node instead of ours.
    const appNode = document.createElement("div");
    appNode.id = "out1";
    appNode.textContent = "app content";
    document.body.insertBefore(appNode, document.body.firstChild);

    const registry = new OutputRegistry();
    const dispose = registry.add("out1", vi.fn(), vi.fn(), vi.fn());
    dispose();
    await new Promise((resolve) => requestAnimationFrame(resolve));

    expect(appNode.isConnected).toBe(true);
    expect(
      document.querySelector(".shiny-react-output-container [id='out1']"),
    ).toBeNull();

    appNode.remove();
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

  it("add syncs new subscriber with the cached value on attach", () => {
    const registry = new OutputRegistry();
    registry.add("out1", vi.fn(), vi.fn(), vi.fn());
    registry.get("out1")!.setValue("first");

    // A subscriber mounting AFTER setValue should see the cached value
    // synchronously, not the default.
    const setVal2 = vi.fn();
    registry.add("out1", setVal2, vi.fn(), vi.fn());
    expect(setVal2).toHaveBeenCalledWith("first");
  });

  it("add does not push value to a new subscriber if no value has been delivered", () => {
    const registry = new OutputRegistry();
    const setVal = vi.fn();
    registry.add("out1", setVal, vi.fn(), vi.fn());
    // Entry exists but never had setValue called → setVal should not fire on attach
    expect(setVal).not.toHaveBeenCalled();
  });

  it("add syncs new subscriber with the cached error on attach when in error state", () => {
    const registry = new OutputRegistry();
    registry.add("out1", vi.fn(), vi.fn(), vi.fn());
    const err = { message: "boom", call: [] };
    registry.get("out1")!.setError(err);

    const setStatus2 = vi.fn();
    const setErr2 = vi.fn();
    registry.add("out1", vi.fn(), setStatus2, setErr2);
    expect(setStatus2).toHaveBeenCalledWith("error");
    expect(setErr2).toHaveBeenCalledWith(err);
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

  it("setRecalculating(true) from error state clears the error", () => {
    const entry = new OutputRegistryEntry("test");
    entry.setValue("first"); // hasValue = true so the recalc transition is allowed
    entry.setError({ message: "boom", call: [] });
    expect(entry.getStatus()).toBe("error");
    expect(entry.getLastError()).not.toBeNull();

    const setError = vi.fn();
    entry.addUseStateSetErrorFn(setError);

    entry.setRecalculating(true);

    expect(entry.getStatus()).toBe("recalculating");
    // Error subscribers must see null so they don't render a stale error
    // while the status is no longer "error".
    expect(setError).toHaveBeenLastCalledWith(null);
    expect(entry.getLastError()).toBeNull();
  });

  it("an empty-message error is a silent error, delivered as a null value", () => {
    // #257. `req()` in R arrives as an error with message "" (vanilla Shiny
    // blanks the output); py-shiny sends a null value for the same `req()`.
    // Both servers must look the same to the React component.
    const entry = new OutputRegistryEntry("test");
    entry.setValue("first");
    const setStatus = vi.fn();
    const setError = vi.fn();
    const setValue = vi.fn();
    entry.addUseStateSetStatusFn(setStatus);
    entry.addUseStateSetErrorFn(setError);
    entry.addUseStateSetValueFn(setValue);

    entry.setError({ message: "", call: [], type: ["shiny.silent.error"] });

    expect(entry.getStatus()).toBe("ready");
    expect(entry.getLastError()).toBeNull();
    expect(setError).not.toHaveBeenCalled();
    expect(setValue).toHaveBeenCalledWith(null);
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
