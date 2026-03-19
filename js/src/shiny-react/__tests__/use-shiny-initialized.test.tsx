import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

// Mutable mock: tests can change what getShiny returns
let mockShiny: any = undefined;
vi.mock("../get-shiny", () => ({
  getShiny: () => mockShiny,
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

import { useShinyInitialized } from "../use-shiny";

async function flushPromises() {
  await act(async () => {
    await new Promise((r) => setTimeout(r, 0));
  });
}

describe("useShinyInitialized", () => {
  beforeEach(() => {
    mockShiny = undefined;
    vi.clearAllMocks();
  });

  afterEach(() => {
    mockShiny = undefined;
  });

  it("returns true when Shiny is already available and initialized", async () => {
    mockShiny = { initializedPromise: Promise.resolve() };

    const { result } = renderHook(() => useShinyInitialized());
    expect(result.current).toBe(false); // initially false

    await flushPromises();
    expect(result.current).toBe(true);
  });

  it("stays false when Shiny is not available and no event fires", () => {
    mockShiny = undefined;

    const { result } = renderHook(() => useShinyInitialized());
    expect(result.current).toBe(false);
  });

  it("resolves via shiny:connected event when Shiny loads late", async () => {
    // Start with no Shiny
    mockShiny = undefined;

    const { result } = renderHook(() => useShinyInitialized());
    expect(result.current).toBe(false);

    // Simulate Shiny loading and firing the connected event
    mockShiny = { initializedPromise: Promise.resolve() };
    await act(async () => {
      document.dispatchEvent(new Event("shiny:connected"));
      await new Promise((r) => setTimeout(r, 0));
    });

    expect(result.current).toBe(true);
  });

  it("cleans up event listener on unmount", () => {
    mockShiny = undefined;

    const addSpy = vi.spyOn(document, "addEventListener");
    const removeSpy = vi.spyOn(document, "removeEventListener");

    const { unmount } = renderHook(() => useShinyInitialized());

    expect(addSpy).toHaveBeenCalledWith(
      "shiny:connected",
      expect.any(Function),
      { once: true },
    );

    unmount();

    expect(removeSpy).toHaveBeenCalledWith(
      "shiny:connected",
      expect.any(Function),
    );

    addSpy.mockRestore();
    removeSpy.mockRestore();
  });

  it("does not update state after unmount (cancelled)", async () => {
    // Use a promise that we control
    let resolveInit!: () => void;
    const initPromise = new Promise<void>((r) => { resolveInit = r; });
    mockShiny = { initializedPromise: initPromise };

    const { result, unmount } = renderHook(() => useShinyInitialized());
    expect(result.current).toBe(false);

    // Unmount before the promise resolves
    unmount();

    // Resolve after unmount — should not cause a state update warning
    await act(async () => {
      resolveInit();
      await new Promise((r) => setTimeout(r, 0));
    });

    // No error thrown, test passes
  });
});
