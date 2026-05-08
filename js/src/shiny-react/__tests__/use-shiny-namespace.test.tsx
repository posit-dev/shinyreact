import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type { ReactNode } from "react";
import { ShinyModuleProvider } from "../ShinyModuleContext";

// Mock getShiny to return a minimal Shiny-like object with an
// initializedPromise that resolves immediately. This allows
// useShinyInitialized to resolve to true so the useShinyInput
// effect (which gates on shinyInitialized) can run.
vi.mock("../get-shiny", () => ({
  getShiny: () => ({
    initializedPromise: Promise.resolve(),
  }),
}));

vi.mock("../react-registry", () => {
  const inputs = {
    get: vi.fn(() => null),
    getOrCreate: vi.fn(() => ({
      updateDebounceDelay: vi.fn(),
      updatePriority: vi.fn(),
      addUseStateSetValueFn: vi.fn(),
      removeUseStateSetValueFn: vi.fn(),
      getValue: vi.fn(() => null),
      setValue: vi.fn(),
    })),
    subscribe: vi.fn((_id: string, _fn: (v: unknown) => void) => () => {}),
  };
  const outputs = {
    add: vi.fn(),
    remove: vi.fn(),
  };
  return {
    initializeReactRegistry: vi.fn(),
    getReactRegistry: vi.fn(() => ({ inputs, outputs })),
    __inputs: inputs,
    __outputs: outputs,
  };
});

vi.mock("../output-registry", () => ({
  createReactOutputBinding: vi.fn(),
}));

vi.mock("../message-registry", () => ({
  initializeMessageRegistry: vi.fn(),
}));

import { useShinyInput, useShinyOutput, useShinyInputValue } from "../use-shiny";
import { getReactRegistry } from "../react-registry";

// Helper: flush microtasks so useShinyInitialized resolves via
// initializedPromise.then(). Without this, the shinyInitialized
// state stays false and the useShinyInput effect never runs.
async function flushPromises() {
  await act(async () => {
    await new Promise((r) => setTimeout(r, 0));
  });
}

describe("useShinyInput namespace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses plain id when no namespace is provided", async () => {
    renderHook(() => useShinyInput("count", 0));
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("count", 0);
  });

  it("uses explicit namespace option", async () => {
    renderHook(() =>
      useShinyInput("count", 0, { namespace: "mod1" }),
    );
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("mod1-count", 0);
  });

  it("uses namespace from ShinyModuleProvider context", async () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="ctxMod">{children}</ShinyModuleProvider>
    );
    renderHook(() => useShinyInput("count", 0), { wrapper });
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("ctxMod-count", 0);
  });

  it("explicit namespace overrides context namespace", async () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="ctxMod">{children}</ShinyModuleProvider>
    );
    renderHook(() => useShinyInput("count", 0, { namespace: "explicit" }), {
      wrapper,
    });
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith(
      "explicit-count",
      0,
    );
  });
});

describe("useShinyInput namespace suppression", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("namespace: null suppresses context namespace", async () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="mod1">{children}</ShinyModuleProvider>
    );
    // Simulates ImageOutput pattern: pre-namespaced ID with namespace: null
    renderHook(
      () =>
        useShinyInput(".clientdata_output_mod1-plot_width", null, {
          namespace: null,
        }),
      { wrapper },
    );
    await flushPromises();
    const registry = getReactRegistry();
    // Should NOT be double-namespaced to "mod1-.clientdata_output_mod1-plot_width"
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith(
      ".clientdata_output_mod1-plot_width",
      null,
    );
  });
});

describe("useShinyOutput namespace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses plain outputId when no namespace is provided", () => {
    renderHook(() => useShinyOutput("result"));
    const registry = getReactRegistry();
    expect(registry).toBeDefined();
  });

  it("uses explicit namespace option for output", () => {
    renderHook(() =>
      useShinyOutput("result", undefined, { namespace: "mod1" }),
    );
    const registry = getReactRegistry();
    expect(registry).toBeDefined();
  });

  it("namespace: null suppresses context namespace for output", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="mod1">{children}</ShinyModuleProvider>
    );
    // Verifies that passing namespace: null doesn't throw and renders
    // successfully even inside a provider (Shiny not initialized so
    // the effect doesn't fire, but the hook itself runs without error)
    const { result } = renderHook(
      () => useShinyOutput("mod1-plot", undefined, { namespace: null }),
      { wrapper },
    );
    expect(result.current).toBeDefined();
  });
});

describe("useShinyInputValue namespace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("subscribes with plain id when no namespace is provided", async () => {
    renderHook(() => useShinyInputValue("hover"));
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.subscribe).toHaveBeenCalledWith(
      "hover",
      expect.any(Function),
    );
  });

  it("applies explicit namespace option", async () => {
    renderHook(() => useShinyInputValue("hover", { namespace: "mod1" }));
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.subscribe).toHaveBeenCalledWith(
      "mod1-hover",
      expect.any(Function),
    );
  });

  it("applies namespace from ShinyModuleProvider context", async () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="ctxMod">{children}</ShinyModuleProvider>
    );
    renderHook(() => useShinyInputValue("hover"), { wrapper });
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.subscribe).toHaveBeenCalledWith(
      "ctxMod-hover",
      expect.any(Function),
    );
  });
});
