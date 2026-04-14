import { describe, expect, it, vi, beforeEach } from "vitest";
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

describe("useShinyBusy", () => {
  beforeEach(() => {
    vi.clearAllMocks();
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

  it("cleans up event listeners on unmount", () => {
    const addSpy = vi.spyOn(document, "addEventListener");
    const removeSpy = vi.spyOn(document, "removeEventListener");

    const { unmount } = renderHook(() => useShinyBusy());

    expect(addSpy).toHaveBeenCalledWith("shiny:busy", expect.any(Function));
    expect(addSpy).toHaveBeenCalledWith("shiny:idle", expect.any(Function));

    unmount();

    expect(removeSpy).toHaveBeenCalledWith("shiny:busy", expect.any(Function));
    expect(removeSpy).toHaveBeenCalledWith("shiny:idle", expect.any(Function));

    addSpy.mockRestore();
    removeSpy.mockRestore();
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
});
