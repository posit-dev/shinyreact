/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, expect, it, beforeEach, vi } from "vitest";

vi.mock("../get-shiny", () => ({
  getShiny: vi.fn(() => undefined),
}));

import { InputRegistry } from "../input-registry";
import { applyRestoredValues } from "../bookmark";

function freshWindow(): void {
  // jsdom provides window; clear any prior shinyreact state.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (globalThis as any).window = (globalThis as any).window || {};
  delete (globalThis as any).window.shinyreact;
}

describe("applyRestoredValues", () => {
  beforeEach(() => {
    freshWindow();
  });

  it("seeds registry entries from window.shinyreact._restore and replaces it with sentinel", () => {
    (window as any).shinyreact = { _restore: { foo: "hello", num: 42 } };
    const registry = new InputRegistry();

    applyRestoredValues(registry);

    expect(registry.get<string>("foo")?.getValue()).toBe("hello");
    expect(registry.get<number>("num")?.getValue()).toBe(42);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": { foo: "hello", num: 42 },
    });
  });

  it("with no _restore set, leaves registry empty and writes empty sentinel", () => {
    (window as any).shinyreact = {};
    const registry = new InputRegistry();

    applyRestoredValues(registry);

    expect(registry.size()).toBe(0);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": {},
    });
  });

  it("with no window.shinyreact at all, creates the namespace and writes sentinel", () => {
    const registry = new InputRegistry();
    applyRestoredValues(registry);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": {},
    });
  });

  it("re-running does not clobber the -values snapshot", () => {
    (window as any).shinyreact = { _restore: { foo: "hello" } };
    const registry = new InputRegistry();

    applyRestoredValues(registry);
    const firstValues = (window as any).shinyreact._restore["-values"];
    applyRestoredValues(registry);
    const secondValues = (window as any).shinyreact._restore["-values"];

    expect(secondValues).toEqual(firstValues);
    expect(secondValues).toEqual({ foo: "hello" });
  });

  it("does not call shiny setInputValue (uses add, not setValue)", () => {
    (window as any).shinyreact = { _restore: { foo: "hello" } };
    const registry = new InputRegistry();
    const entry = vi.spyOn(registry, "add");

    applyRestoredValues(registry);

    // We use add() so the value is stored without invoking
    // shinySetInputValueDebounced. The first useShinyInput mount will
    // re-broadcast through setValue() at the existing path.
    expect(entry).toHaveBeenCalledWith("foo", "hello");
  });

  it("drains pendingSubscribers when seeding via add()", () => {
    (window as any).shinyreact = { _restore: { foo: "hello" } };
    const registry = new InputRegistry();
    const subscriber = vi.fn();
    // Subscribe before the producer adds — should queue in pendingSubscribers.
    const unsub = registry.subscribe<string>("foo", subscriber);

    applyRestoredValues(registry);

    expect(subscriber).toHaveBeenCalledWith("hello");
    unsub();
  });
});
