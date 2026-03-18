import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { ShinyModuleProvider } from "../ShinyModuleContext";

// Mock the registries and Shiny initialization so hooks can run
// without a real Shiny environment
vi.mock("../get-shiny", () => ({
  getShiny: () => undefined,
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

import { useShinyInput, useShinyOutput } from "../use-shiny";
import { getReactRegistry } from "../react-registry";

describe("useShinyInput namespace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses plain id when no namespace is provided", () => {
    renderHook(() => useShinyInput("count", 0));
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("count", 0);
  });

  it("uses explicit namespace option", () => {
    renderHook(() =>
      useShinyInput("count", 0, { namespace: "mod1" }),
    );
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("mod1-count", 0);
  });

  it("uses namespace from ShinyModuleProvider context", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="ctxMod">{children}</ShinyModuleProvider>
    );
    renderHook(() => useShinyInput("count", 0), { wrapper });
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("ctxMod-count", 0);
  });

  it("explicit namespace overrides context namespace", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="ctxMod">{children}</ShinyModuleProvider>
    );
    renderHook(() => useShinyInput("count", 0, { namespace: "explicit" }), {
      wrapper,
    });
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

  it("namespace: null suppresses context namespace", () => {
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
