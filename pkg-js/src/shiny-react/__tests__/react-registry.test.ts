/* eslint-disable @typescript-eslint/no-explicit-any */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  _resetReactRegistryForTesting,
  getReactRegistry,
  initializeReactRegistry,
} from "../react-registry";

function fakeShiny() {
  return {
    reactRegistry: undefined as unknown,
    addCustomMessageHandler: vi.fn(),
    setInputValue: vi.fn(),
    outputBindings: { register: vi.fn() },
    OutputBinding: class {},
  };
}

beforeEach(() => {
  _resetReactRegistryForTesting();
  delete (window as any).Shiny;
});

afterEach(() => {
  delete (window as any).Shiny;
});

describe("getReactRegistry", () => {
  it("returns the module registries when there is no Shiny", () => {
    const first = getReactRegistry();

    expect(first.inputs).toBeDefined();
    expect(first.outputs).toBeDefined();
    expect(getReactRegistry()).toBe(first);
  });

  it("attaches to window.Shiny on first use", () => {
    const shiny = fakeShiny();
    (window as any).Shiny = shiny;

    const registry = getReactRegistry();

    expect(shiny.reactRegistry).toBe(registry);
  });

  it("adopts a registry another copy of the library already attached", async () => {
    const shiny = fakeShiny();
    (window as any).Shiny = shiny;
    const first = getReactRegistry();
    first.inputs.add("shared", 1);

    // A second copy of the library: fresh module state, same page.
    vi.resetModules();
    const second = await import("../react-registry");

    expect(second.getReactRegistry()).toBe(first);
    expect(second.getReactRegistry().inputs.get("shared")?.getValue()).toBe(1);
  });

  it("never returns undefined when Shiny is present but init never ran", () => {
    // The old implementation read `shiny.reactRegistry` unchecked, so this
    // returned undefined and crashed one call later, far from the cause.
    (window as any).Shiny = fakeShiny();

    expect(getReactRegistry()).toBeDefined();
  });
});

describe("initializeReactRegistry", () => {
  it("is idempotent — a second call keeps existing values", () => {
    // It used to rebuild both registries, silently discarding every input value
    // and output subscriber the page had accumulated.
    (window as any).Shiny = fakeShiny();
    initializeReactRegistry();
    getReactRegistry().inputs.add("keep-me", 42);

    initializeReactRegistry();

    expect(getReactRegistry().inputs.get("keep-me")?.getValue()).toBe(42);
  });
});
