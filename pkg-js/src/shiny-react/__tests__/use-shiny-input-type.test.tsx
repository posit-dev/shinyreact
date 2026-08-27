/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, cleanup, render } from "@testing-library/react";
import * as React from "react";

// Mock getShiny so the hook's useShinyInitialized resolves to true via
// `initializedPromise`, and so we can capture setInputValue calls.
// IMPORTANT: the mock must always return the *same* object so that
// initializeReactRegistry() and getReactRegistry() both see the same
// `shiny.reactRegistry` reference.
const mockSetInputValue = vi.fn();
const mockShiny: Record<string, any> = {
  initializedPromise: Promise.resolve(),
  setInputValue: mockSetInputValue,
};
vi.mock("../get-shiny", () => ({
  getShiny: vi.fn(() => mockShiny),
}));

// Mock output-registry and message-registry so ensureShinyReactInitialized
// doesn't blow up trying to use shiny.OutputBinding (undefined in tests).
// Keep the real exports (OutputRegistry class etc.) via importOriginal so that
// initializeReactRegistry() can still construct `new OutputRegistry()`.
vi.mock("../output-registry", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../output-registry")>();
  return {
    ...actual,
    createReactOutputBinding: vi.fn(),
  };
});
vi.mock("../message-registry", () => ({
  initializeMessageRegistry: vi.fn(),
}));

import { _resetReactRegistryForTesting } from "../react-registry";
import {
  _resetShinyReactInitializedForTesting,
  useSetShinyInput,
  useShinyInput,
} from "../use-shiny";
import { ShinyModuleProvider } from "../ShinyModuleContext";

function freshState(): void {
  (globalThis as any).window = (globalThis as any).window || {};
  delete (globalThis as any).window.shinyreact;
  // Clear the reactRegistry that initializeReactRegistry() attaches to the
  // mock shiny object, so each test starts with a fresh InputRegistry.
  delete mockShiny.reactRegistry;
  // Also drop the module-local registries: initializeReactRegistry() is
  // idempotent now, so deleting the window property alone no longer gives a
  // fresh InputRegistry.
  _resetReactRegistryForTesting();
  _resetShinyReactInitializedForTesting();
}

// Helper: flush microtasks + timers so useShinyInitialized resolves and the
// debounced setInputValue fires.
async function flushAll() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
  await act(async () => {
    vi.advanceTimersByTime(200);
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
  freshState();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

function ProducerFull({
  id,
  type,
  initial = 0,
}: {
  id: string;
  type?: string;
  initial?: number;
}) {
  const [value, setValue] = useShinyInput<number>(id, initial, {
    debounceMs: 0,
    ...(type !== undefined ? { type } : {}),
  });
  return (
    <button data-testid={`btn-${id}`} onClick={() => setValue(value + 1)}>
      {value}
    </button>
  );
}

function ProducerSet({
  id,
  type,
  initial = 0,
}: {
  id: string;
  type?: string;
  initial?: number;
}) {
  const setValue = useSetShinyInput<number>(id, initial, {
    debounceMs: 0,
    ...(type !== undefined ? { type } : {}),
  });
  return <button data-testid={`set-${id}`} onClick={() => setValue(initial + 1)} />;
}

describe("useShinyInput / useSetShinyInput — `type` option", () => {
  it("appends suffix when type is set", async () => {
    render(<ProducerFull id="foo" type="shiny.datetime" />);
    await flushAll();

    act(() => {
      document.querySelector<HTMLButtonElement>("[data-testid=btn-foo]")!.click();
    });
    await flushAll();

    const calls = mockSetInputValue.mock.calls.filter((c) => c[0].startsWith("foo"));
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      expect(call[0]).toBe("foo:shiny.datetime");
    }
  });

  it("uses the shinyreact.default suffix when type is not set", async () => {
    render(<ProducerFull id="foo" />);
    await flushAll();

    act(() => {
      document.querySelector<HTMLButtonElement>("[data-testid=btn-foo]")!.click();
    });
    await flushAll();

    const calls = mockSetInputValue.mock.calls.filter((c) => c[0].startsWith("foo"));
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      expect(call[0]).toBe("foo:shinyreact.default");
    }
  });

  it.each([
    ["", /invalid type=/],
    ["has space", /invalid type=/],
    ["a:b", /invalid type=/],
  ])("throws synchronously on invalid type=%j", (badType, pattern) => {
    // Suppress React's error logging for the expected throw.
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() =>
      render(<ProducerFull id="bad" type={badType} />),
    ).toThrow(pattern as RegExp);
    errorSpy.mockRestore();
  });

  it("conflicting types across two mounts: second mount throws", async () => {
    // First mount: type "X" — finalizes the registry entry.
    const { unmount: unmountA } = render(<ProducerFull id="conf" type="X" />);
    await flushAll();

    // Second mount with a conflicting type: React surfaces the throw from
    // the useEffect through render(). Use a try/catch.
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    let caught: Error | undefined;
    try {
      render(<ProducerFull id="conf" type="Y" />);
      await flushAll();
    } catch (e) {
      caught = e as Error;
    }
    errorSpy.mockRestore();

    // The conflict throw must have surfaced (either synchronously from render
    // or via the act-flushed effect — both routes acceptable, but it must
    // appear somewhere).
    const sawConflict =
      (caught && /already registered with type="X"/.test(caught.message)) ||
      (errorSpy.mock.calls.flat().some((arg) =>
        typeof arg === "string"
          ? /already registered with type="X"/.test(arg)
          : arg instanceof Error
            ? /already registered with type="X"/.test(arg.message)
            : false,
      ));
    expect(sawConflict).toBe(true);

    // First mount's wire calls remained "conf:X".
    const calls = mockSetInputValue.mock.calls.filter((c) =>
      typeof c[0] === "string" && c[0].startsWith("conf"),
    );
    for (const call of calls) {
      expect(call[0]).toBe("conf:X");
    }

    unmountA();
  });

  it("later mount omitting type is fine", async () => {
    render(<ProducerFull id="omit" type="X" />);
    await flushAll();

    // Second mount: no type — should NOT throw.
    expect(() => render(<ProducerSet id="omit" />)).not.toThrow();
    await flushAll();
  });

  it("adding a type after a no-type mount throws", async () => {
    render(<ProducerFull id="late" />);
    await flushAll();

    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    let caught: Error | undefined;
    try {
      render(<ProducerFull id="late" type="X" />);
      await flushAll();
    } catch (e) {
      caught = e as Error;
    }
    errorSpy.mockRestore();

    const sawConflict =
      (caught && /already registered with type=undefined/.test(caught.message)) ||
      (errorSpy.mock.calls.flat().some((arg) =>
        typeof arg === "string"
          ? /already registered with type=undefined/.test(arg)
          : arg instanceof Error
            ? /already registered with type=undefined/.test(arg.message)
            : false,
      ));
    expect(sawConflict).toBe(true);
  });

  it("namespacing: wire id is `ns-foo:shiny.datetime`", async () => {
    render(
      <ShinyModuleProvider namespace="ns">
        <ProducerFull id="foo" type="shiny.datetime" />
      </ShinyModuleProvider>,
    );
    await flushAll();

    act(() => {
      document.querySelector<HTMLButtonElement>("[data-testid=btn-foo]")!.click();
    });
    await flushAll();

    const calls = mockSetInputValue.mock.calls.filter(
      (c) => typeof c[0] === "string" && c[0].startsWith("ns-foo"),
    );
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      expect(call[0]).toBe("ns-foo:shiny.datetime");
    }
  });

  it("useSetShinyInput appends suffix when type is set", async () => {
    render(<ProducerSet id="setfoo" type="shiny.datetime" initial={5} />);
    await flushAll();

    act(() => {
      document.querySelector<HTMLButtonElement>("[data-testid=set-setfoo]")!.click();
    });
    await flushAll();

    const calls = mockSetInputValue.mock.calls.filter(
      (c) => typeof c[0] === "string" && c[0].startsWith("setfoo"),
    );
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      expect(call[0]).toBe("setfoo:shiny.datetime");
    }
  });
});

