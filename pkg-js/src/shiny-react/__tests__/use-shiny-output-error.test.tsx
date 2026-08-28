import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ErrorsMessageValue } from "../output-registry";
import {
  _resetReactRegistryForTesting,
  getReactRegistry,
} from "../react-registry";
import {
  _resetShinyReactInitializedForTesting,
  useShinyOutputError,
} from "../use-shiny";

// Same stand-in as use-shiny-output-value.test.tsx: resolve initializedPromise
// immediately so the hook's effect runs, and let the real OutputRegistry play
// the other half of the interaction under test.
vi.mock("../get-shiny", () => ({
  getShiny: () => ({
    initializedPromise: Promise.resolve(),
    outputBindings: { register: () => {} },
    OutputBinding: class {},
    addCustomMessageHandler: () => {},
    bindAll: () => {},
    unbindAll: () => {},
  }),
}));

beforeEach(() => {
  _resetReactRegistryForTesting();
  _resetShinyReactInitializedForTesting();
});

afterEach(() => {
  document
    .querySelectorAll(".shiny-react-output-container")
    .forEach((el) => el.remove());
});

async function flush(): Promise<void> {
  await act(async () => {
    await Promise.resolve();
  });
}

const boom: ErrorsMessageValue = {
  message: "invalid number of 'breaks'",
  call: ["hist(x, breaks = n)"],
  type: undefined,
};

describe("useShinyOutputError", () => {
  it("starts at null and delivers the server's error message", async () => {
    const registry = getReactRegistry();
    const { result } = renderHook(() => useShinyOutputError("out"));
    await flush();
    expect(result.current).toBeNull();

    act(() => registry.outputs.get("out")!.setError(boom));
    await flush();

    expect(result.current).toEqual(boom);
  });

  it("syncs a late-mounting subscriber with the cached error", async () => {
    const registry = getReactRegistry();
    registry.outputs.add(
      "out",
      () => {},
      () => {},
      () => {},
    );
    registry.outputs.get("out")!.setError(boom);

    const { result } = renderHook(() => useShinyOutputError("out"));
    await flush();

    expect(result.current).toEqual(boom);
  });

  it("clears when a value arrives", async () => {
    const registry = getReactRegistry();
    const { result } = renderHook(() => useShinyOutputError("out"));
    await flush();

    act(() => registry.outputs.get("out")!.setError(boom));
    await flush();
    act(() => registry.outputs.get("out")!.setValue("recovered"));
    await flush();

    expect(result.current).toBeNull();
  });

  it("stays null for a silent error", async () => {
    const registry = getReactRegistry();
    const { result } = renderHook(() => useShinyOutputError("out"));
    await flush();

    act(() =>
      registry.outputs
        .get("out")!
        .setError({ message: "", call: [], type: ["shiny.silent.error"] }),
    );
    await flush();

    expect(result.current).toBeNull();
  });

  it("drops the previous id's error when the id changes", async () => {
    const registry = getReactRegistry();
    const { result, rerender } = renderHook(
      ({ id }: { id: string }) => useShinyOutputError(id),
      { initialProps: { id: "first" } },
    );
    await flush();

    act(() => registry.outputs.get("first")!.setError(boom));
    await flush();
    expect(result.current).toEqual(boom);

    rerender({ id: "second" });
    await flush();

    expect(result.current).toBeNull();
  });
});
