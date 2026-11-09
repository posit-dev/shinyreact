import { act, render } from "@testing-library/react";
import {
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

// Mock getShiny so useShinyInitialized resolves immediately and child
// hooks' init-gated effects can run.
vi.mock("../get-shiny", () => ({
  getShiny: () => ({ initializedPromise: Promise.resolve() }),
}));

vi.mock("../react-registry", () => {
  const inputEntry = {
    updateDebounceDelay: vi.fn(),
    updatePriority: vi.fn(),
    updateType: vi.fn(),
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
import { __resetLifecycleStoreForTests } from "../lifecycle-store";
import { ShinyModuleProvider } from "../ShinyModuleContext";
import { getReactRegistry } from "../react-registry";

beforeAll(() => {
  // ImageOutput attaches a ResizeObserver. jsdom doesn't ship one — stub it
  // so the component can mount without throwing.
  (globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver =
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
});

beforeEach(() => {
  // useShinyInitialized reads from the module-scoped lifecycle store, which
  // latches `initialized = true` after the first hook resolves. Reset so each
  // test starts from a known state and is independent of test order.
  __resetLifecycleStoreForTests();
  vi.clearAllMocks();
});

afterEach(() => {
  __resetLifecycleStoreForTests();
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

// Drive an output the way the real registry would: `outputs.add(id, setValue,
// setStatus, setError)` hands the hook its setters, so keep the latest ones per
// id and call them.
function captureOutputSetters() {
  const setters = new Map<
    string,
    { value: (v: unknown) => void; error: (e: unknown) => void }[]
  >();
  const reg = getReactRegistry();
  (reg.outputs.add as ReturnType<typeof vi.fn>).mockImplementation(
    (
      id: string,
      value: (v: unknown) => void,
      _status: unknown,
      error: (e: unknown) => void,
    ) => {
      setters.set(id, [...(setters.get(id) ?? []), { value, error }]);
      return () => {};
    },
  );
  return {
    sendValue: (id: string, v: unknown) =>
      act(() => setters.get(id)!.forEach((s) => s.value(v))),
    sendError: (id: string, e: unknown) =>
      act(() => setters.get(id)!.forEach((s) => s.error(e))),
  };
}

const IMG = { src: "data:image/png;base64,AAAA", width: 4, height: 3 };

describe("ImageOutput image data", () => {
  it("uses the renderer's alt text", async () => {
    // #327: alt="" was hardcoded, ignoring renderPlot(alt =).
    const out = captureOutputSetters();
    const { container } = render(<ImageOutput id="plot" />);
    await flushPromises();
    out.sendValue("plot", { ...IMG, alt: "A scatterplot" });
    expect(container.querySelector("img")!.getAttribute("alt")).toBe(
      "A scatterplot",
    );
  });

  it("falls back to an empty alt when the renderer sends none", async () => {
    const out = captureOutputSetters();
    const { container } = render(<ImageOutput id="plot" />);
    await flushPromises();
    out.sendValue("plot", IMG);
    expect(container.querySelector("img")!.getAttribute("alt")).toBe("");
  });
});

describe("ImageOutput on error", () => {
  it("hides the stale image and shows the message with Shiny's classes", async () => {
    // #327: the last image stayed on screen and the message appeared nowhere.
    const out = captureOutputSetters();
    const { container } = render(<ImageOutput id="plot" className="mine" />);
    await flushPromises();
    out.sendValue("plot", IMG);
    expect(container.querySelector("img")).not.toBeNull();

    out.sendError("plot", {
      message: "Nothing to plot",
      call: null,
      type: ["shiny.silent.error", "validation"],
    });

    expect(container.querySelector("img")).toBeNull();
    const el = container.firstElementChild!;
    expect(el.textContent).toBe("Nothing to plot");
    expect([...el.classList]).toEqual([
      "shiny-output-error",
      "shiny-output-error-shiny.silent.error",
      "shiny-output-error-validation",
      "mine",
    ]);
  });

  it("accepts an R one-class type unboxed to a string", async () => {
    const out = captureOutputSetters();
    const { container } = render(<ImageOutput id="plot" />);
    await flushPromises();
    out.sendError("plot", { message: "boom", call: null, type: "validation" });
    expect(container.firstElementChild!.className).toBe(
      "shiny-output-error shiny-output-error-validation",
    );
  });

  it("shows the image again once the error clears", async () => {
    const out = captureOutputSetters();
    const { container } = render(<ImageOutput id="plot" />);
    await flushPromises();
    out.sendError("plot", { message: "boom", call: null, type: null });
    expect(container.querySelector("img")).toBeNull();

    out.sendError("plot", null);
    out.sendValue("plot", IMG);
    expect(container.querySelector("img")).not.toBeNull();
    expect(container.textContent).not.toContain("boom");
  });
});
