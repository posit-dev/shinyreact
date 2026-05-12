import { act, render } from "@testing-library/react";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

// Mock getShiny so useShinyInitialized resolves immediately and child
// hooks' init-gated effects can run.
vi.mock("../get-shiny", () => ({
  getShiny: () => ({ initializedPromise: Promise.resolve() }),
}));

vi.mock("../react-registry", () => {
  const inputEntry = {
    updateDebounceDelay: vi.fn(),
    updatePriority: vi.fn(),
    addUseStateSetValueFn: vi.fn(),
    removeUseStateSetValueFn: vi.fn(),
    getValue: vi.fn(() => null),
    setValue: vi.fn(),
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
  };
});

vi.mock("../output-registry", () => ({
  createReactOutputBinding: vi.fn(),
}));

vi.mock("../message-registry", () => ({
  initializeMessageRegistry: vi.fn(),
}));

import { ImageOutput } from "../ImageOutput";
import { ShinyModuleProvider } from "../ShinyModuleContext";
import { getReactRegistry } from "../react-registry";

beforeAll(() => {
  // ImageOutput attaches a ResizeObserver. jsdom doesn't ship one — stub it
  // so the component can mount without throwing.
  (globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

beforeEach(() => {
  vi.clearAllMocks();
});

async function flushPromises() {
  // useShinyInput gates its registry call on useShinyInitialized resolving via
  // initializedPromise.then(); flush the microtask queue so that effect runs.
  await act(async () => {
    await new Promise((r) => setTimeout(r, 0));
  });
}

function registeredIds() {
  const reg = getReactRegistry();
  return (reg.inputs.getOrCreate as ReturnType<typeof vi.fn>).mock.calls.map(
    (call) => call[0] as string,
  );
}

describe("ImageOutput namespace precedence", () => {
  it("applies the provider context namespace by default", async () => {
    render(
      <ShinyModuleProvider namespace="ctx">
        <ImageOutput id="myimg" />
      </ShinyModuleProvider>,
    );
    await flushPromises();
    const ids = registeredIds();
    expect(ids).toContain(".clientdata_output_ctx-myimg_width");
    expect(ids).toContain(".clientdata_output_ctx-myimg_height");
    expect(ids).toContain(".clientdata_output_ctx-myimg_hidden");
  });

  it("explicit namespace prop overrides the provider context", async () => {
    render(
      <ShinyModuleProvider namespace="ctx">
        <ImageOutput id="myimg" namespace="explicit" />
      </ShinyModuleProvider>,
    );
    await flushPromises();
    const ids = registeredIds();
    expect(ids).toContain(".clientdata_output_explicit-myimg_width");
    expect(ids).not.toContain(".clientdata_output_ctx-myimg_width");
  });

  it("namespace={null} opts out of the provider context", async () => {
    // Regression guard for the `??` → `!== undefined` precedence fix.
    // With `??`, `null` would be conflated with `undefined` and silently
    // fall through to the context — registering ".clientdata_output_ctx-…"
    // instead of the bare id the caller asked for.
    render(
      <ShinyModuleProvider namespace="ctx">
        <ImageOutput id="myimg" namespace={null} />
      </ShinyModuleProvider>,
    );
    await flushPromises();
    const ids = registeredIds();
    expect(ids).toContain(".clientdata_output_myimg_width");
    expect(ids).not.toContain(".clientdata_output_ctx-myimg_width");
  });
});
