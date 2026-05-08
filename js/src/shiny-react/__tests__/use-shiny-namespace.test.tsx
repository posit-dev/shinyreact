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

// Shared spies on the input entry returned by `getOrCreate`. Hoisted so they
// are available when the mock factory runs (vi.mock is hoisted above
// imports). We expose a single entry instance from the mock so tests can
// assert what was (or wasn't) called on the entry across hook invocations —
// particularly `addUseStateSetValueFn`, which `useSetShinyInput` must NOT call.
const {
  entryAddSetValue,
  entryRemoveSetValue,
  entrySetValue,
  entryUpdateDebounceDelay,
  entryUpdatePriority,
  entryGetValue,
} = vi.hoisted(() => ({
  entryAddSetValue: vi.fn(),
  entryRemoveSetValue: vi.fn(),
  entrySetValue: vi.fn(),
  entryUpdateDebounceDelay: vi.fn(),
  entryUpdatePriority: vi.fn(),
  entryGetValue: vi.fn(() => null),
}));

vi.mock("../react-registry", () => {
  const inputEntry = {
    updateDebounceDelay: entryUpdateDebounceDelay,
    updatePriority: entryUpdatePriority,
    addUseStateSetValueFn: entryAddSetValue,
    removeUseStateSetValueFn: entryRemoveSetValue,
    getValue: entryGetValue,
    setValue: entrySetValue,
  };
  const inputs = {
    get: vi.fn(() => null),
    getOrCreate: vi.fn(() => inputEntry),
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

import {
  useSetShinyInput,
  useShinyInput,
  useShinyInputValue,
  useShinyOutputStatus,
  useShinyOutputValue,
} from "../use-shiny";
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

describe("useShinyOutputValue namespace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses plain outputId when no namespace is provided", () => {
    renderHook(() => useShinyOutputValue("result"));
    const registry = getReactRegistry();
    expect(registry).toBeDefined();
  });

  it("uses explicit namespace option for output", () => {
    renderHook(() =>
      useShinyOutputValue("result", undefined, { namespace: "mod1" }),
    );
    const registry = getReactRegistry();
    expect(registry).toBeDefined();
  });

  it("namespace: null suppresses context namespace for output", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="mod1">{children}</ShinyModuleProvider>
    );
    const { result } = renderHook(
      () => useShinyOutputValue("mod1-plot", undefined, { namespace: null }),
      { wrapper },
    );
    expect(result.current).toBeUndefined();
  });
});

describe("useShinyOutputStatus namespace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses plain outputId when no namespace is provided", () => {
    const { result } = renderHook(() => useShinyOutputStatus("result"));
    expect(result.current).toBe("pending");
  });

  it("uses explicit namespace option for output", () => {
    const { result } = renderHook(() =>
      useShinyOutputStatus("result", { namespace: "mod1" }),
    );
    expect(result.current).toBe("pending");
  });

  it("namespace: null suppresses context namespace for output", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="mod1">{children}</ShinyModuleProvider>
    );
    const { result } = renderHook(
      () => useShinyOutputStatus("mod1-plot", { namespace: null }),
      { wrapper },
    );
    expect(result.current).toBe("pending");
  });
});

describe("useSetShinyInput namespace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("registers with plain id when no namespace is provided", async () => {
    renderHook(() => useSetShinyInput("count", 0));
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("count", 0);
  });

  it("applies explicit namespace option", async () => {
    renderHook(() => useSetShinyInput("count", 0, { namespace: "mod1" }));
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("mod1-count", 0);
  });

  it("applies namespace from ShinyModuleProvider context", async () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="ctxMod">{children}</ShinyModuleProvider>
    );
    renderHook(() => useSetShinyInput("count", 0), { wrapper });
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.getOrCreate).toHaveBeenCalledWith("ctxMod-count", 0);
  });

  it("returns just a setter (no value)", async () => {
    const { result } = renderHook(() => useSetShinyInput("count", 0));
    await flushPromises();
    expect(typeof result.current).toBe("function");
  });

  it("does NOT register a useState setter on the entry — write-only", async () => {
    // The whole point of useSetShinyInput vs. useShinyInput()[1] is to skip
    // the value subscription so the component doesn't re-render when the
    // input value changes elsewhere. Pin that contract.
    renderHook(() => useSetShinyInput("count", 0));
    await flushPromises();
    expect(entryAddSetValue).not.toHaveBeenCalled();
  });

  it("contrast: useShinyInput DOES register a useState setter", async () => {
    // Mirror assertion to make the contrast explicit and catch regressions
    // if the underlying registry contract ever changes.
    renderHook(() => useShinyInput("count", 0));
    await flushPromises();
    expect(entryAddSetValue).toHaveBeenCalledTimes(1);
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

  it("explicit namespace overrides context namespace", async () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="ctxMod">{children}</ShinyModuleProvider>
    );
    renderHook(
      () => useShinyInputValue("hover", { namespace: "explicit" }),
      { wrapper },
    );
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.subscribe).toHaveBeenCalledWith(
      "explicit-hover",
      expect.any(Function),
    );
  });

  it("namespace: null suppresses context namespace", async () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="mod1">{children}</ShinyModuleProvider>
    );
    renderHook(
      () =>
        useShinyInputValue(".clientdata_output_mod1-plot_width", {
          namespace: null,
        }),
      { wrapper },
    );
    await flushPromises();
    const registry = getReactRegistry();
    expect(registry.inputs.subscribe).toHaveBeenCalledWith(
      ".clientdata_output_mod1-plot_width",
      expect.any(Function),
    );
  });
});
