import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

vi.mock("../get-shiny", () => ({
  getShiny: () => undefined,
}));

vi.mock("../react-registry", () => ({
  initializeReactRegistry: vi.fn(),
  getReactRegistry: vi.fn(() => ({
    inputs: { get: vi.fn(), getOrCreate: vi.fn() },
    outputs: { add: vi.fn(), remove: vi.fn() },
  })),
}));

vi.mock("../output-registry", () => ({
  createReactOutputBinding: vi.fn(),
}));

vi.mock("../message-registry", () => ({
  initializeMessageRegistry: vi.fn(),
}));

import { useShinyBusy } from "../use-shiny";
import { __resetLifecycleStoreForTests } from "../lifecycle-store";

describe("useShinyBusy", () => {
  beforeEach(() => {
    __resetLifecycleStoreForTests();
    document.documentElement.classList.remove("shiny-busy");
    vi.clearAllMocks();
  });

  afterEach(() => {
    __resetLifecycleStoreForTests();
    document.documentElement.classList.remove("shiny-busy");
  });

  it("returns false initially", () => {
    const { result } = renderHook(() => useShinyBusy());
    expect(result.current).toBe(false);
  });

  it("returns true after shiny:busy event", () => {
    const { result } = renderHook(() => useShinyBusy());

    act(() => {
      document.dispatchEvent(new Event("shiny:busy"));
    });

    expect(result.current).toBe(true);
  });

  it("returns false after shiny:idle event following busy", () => {
    const { result } = renderHook(() => useShinyBusy());

    act(() => {
      document.dispatchEvent(new Event("shiny:busy"));
    });
    expect(result.current).toBe(true);

    act(() => {
      document.dispatchEvent(new Event("shiny:idle"));
    });
    expect(result.current).toBe(false);
  });

  it("handles multiple busy/idle cycles", () => {
    const { result } = renderHook(() => useShinyBusy());

    for (let i = 0; i < 3; i++) {
      act(() => {
        document.dispatchEvent(new Event("shiny:busy"));
      });
      expect(result.current).toBe(true);

      act(() => {
        document.dispatchEvent(new Event("shiny:idle"));
      });
      expect(result.current).toBe(false);
    }
  });

  it("does not respond to events after unmount", () => {
    const { result, unmount } = renderHook(() => useShinyBusy());

    unmount();

    // Dispatching after unmount should not cause errors
    act(() => {
      document.dispatchEvent(new Event("shiny:busy"));
    });

    // result.current retains the last value before unmount
    expect(result.current).toBe(false);
  });

  it("seeds busy=true when .shiny-busy is already on documentElement at first mount", () => {
    document.documentElement.classList.add("shiny-busy");

    const { result } = renderHook(() => useShinyBusy());

    expect(result.current).toBe(true);
  });

  it("shares one DOM subscription across many consumers", () => {
    const addSpy = vi.spyOn(document, "addEventListener");

    // Mount many consumers — only the first should attach DOM listeners.
    const hooks = Array.from({ length: 5 }, () =>
      renderHook(() => useShinyBusy()),
    );

    const busyAdds = addSpy.mock.calls.filter((c) => c[0] === "shiny:busy");
    const idleAdds = addSpy.mock.calls.filter((c) => c[0] === "shiny:idle");
    expect(busyAdds).toHaveLength(1);
    expect(idleAdds).toHaveLength(1);

    // All consumers see the same value.
    hooks.forEach((h) => expect(h.result.current).toBe(false));

    act(() => {
      document.dispatchEvent(new Event("shiny:busy"));
    });
    hooks.forEach((h) => expect(h.result.current).toBe(true));

    act(() => {
      document.dispatchEvent(new Event("shiny:idle"));
    });
    hooks.forEach((h) => expect(h.result.current).toBe(false));

    addSpy.mockRestore();
  });
});
