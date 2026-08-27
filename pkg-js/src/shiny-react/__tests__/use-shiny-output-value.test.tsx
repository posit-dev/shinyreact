/* eslint-disable @typescript-eslint/no-explicit-any */
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { _resetReactRegistryForTesting, getReactRegistry } from "../react-registry";
import {
  _resetShinyReactInitializedForTesting,
  useShinyOutputValue,
} from "../use-shiny";

// A Shiny stand-in whose initializedPromise resolves immediately, so the
// hook's effect (gated on shinyInitialized) runs. Deliberately NOT mocking the
// registry: the behavior under test is how the hook and the real
// OutputRegistry interact when the subscribed id changes.
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

describe("useShinyOutputValue when the id changes", () => {
  it("drops the previous id's value instead of showing it as the new id's", async () => {
    // #223 item 17. `outputs.add()` only pushes a value when the new entry has
    // already received one, so without an explicit reset an id the server has
    // not answered yet kept rendering the *other* output's data.
    const registry = getReactRegistry();
    const { result, rerender } = renderHook(
      ({ id }: { id: string }) => useShinyOutputValue<string>(id),
      { initialProps: { id: "first" } },
    );
    await flush();

    registry.outputs.get("first")!.setValue("first value");
    await flush();
    expect(result.current).toBe("first value");

    rerender({ id: "second" });
    await flush();

    expect(result.current).toBeUndefined();
  });

  it("falls back to the caller's defaultValue on an id change", async () => {
    const registry = getReactRegistry();
    const { result, rerender } = renderHook(
      ({ id }: { id: string }) => useShinyOutputValue<string>(id, "waiting"),
      { initialProps: { id: "first" } },
    );
    await flush();

    registry.outputs.get("first")!.setValue("first value");
    await flush();
    expect(result.current).toBe("first value");

    rerender({ id: "second" });
    await flush();

    expect(result.current).toBe("waiting");
  });

  it("adopts the new id's cached value when the server already answered it", async () => {
    // The reset must not clobber a value the registry can supply immediately.
    const registry = getReactRegistry();
    registry.outputs.add(
      "second",
      () => {},
      () => {},
      () => {},
    );
    registry.outputs.get("second")!.setValue("second value");

    const { result, rerender } = renderHook(
      ({ id }: { id: string }) => useShinyOutputValue<string>(id),
      { initialProps: { id: "first" } },
    );
    await flush();
    rerender({ id: "second" });
    await flush();

    expect(result.current).toBe("second value");
  });
});
