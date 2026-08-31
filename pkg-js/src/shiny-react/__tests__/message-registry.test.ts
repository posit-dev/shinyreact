/* eslint-disable @typescript-eslint/no-explicit-any */
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  getMessageRegistry,
  initializeMessageRegistry,
  ShinyMessageRegistry,
} from "../message-registry";

type Dispatcher = (msg: { id: string; data: unknown }) => void;

/** A minimal `window.Shiny` that records the custom-message dispatcher. */
function fakeShiny() {
  const handlers = new Map<string, Dispatcher>();
  return {
    // Present so the attach in getMessageRegistry() type-checks against this
    // stand-in the way it does against ShinyClassExtended.
    messageRegistry: undefined as unknown,
    addCustomMessageHandler: vi.fn((type: string, fn: Dispatcher) => {
      handlers.set(type, fn);
    }),
    /** Simulate the server sending a `shinyReactMessage`. */
    send(id: string, data: unknown) {
      handlers.get("shinyReactMessage")?.({ id, data });
    },
  };
}

beforeEach(() => {
  delete (window as any).Shiny;
});

describe("ShinyMessageRegistry", () => {
  it("registers one dispatcher with Shiny, lazily on the first addHandler", () => {
    const shiny = fakeShiny();
    (window as any).Shiny = shiny;
    const registry = new ShinyMessageRegistry();

    expect(shiny.addCustomMessageHandler).not.toHaveBeenCalled();

    registry.addHandler("a", vi.fn());
    registry.addHandler("b", vi.fn());

    expect(shiny.addCustomMessageHandler).toHaveBeenCalledTimes(1);
    expect(shiny.addCustomMessageHandler.mock.calls[0][0]).toBe(
      "shinyReactMessage",
    );
  });

  it("routes a message to every handler registered for its id", () => {
    const shiny = fakeShiny();
    (window as any).Shiny = shiny;
    const registry = new ShinyMessageRegistry();
    const first = vi.fn();
    const second = vi.fn();
    const other = vi.fn();

    registry.addHandler("greet", first);
    registry.addHandler("greet", second);
    registry.addHandler("elsewhere", other);

    shiny.send("greet", { text: "hi" });

    expect(first).toHaveBeenCalledWith({ text: "hi" });
    expect(second).toHaveBeenCalledWith({ text: "hi" });
    expect(other).not.toHaveBeenCalled();
  });

  it("stops calling a removed handler, and drops the id when the last one goes", () => {
    (window as any).Shiny = fakeShiny();
    const registry = new ShinyMessageRegistry();
    const handler = vi.fn();

    registry.addHandler("id", handler);
    expect(registry.getHandlerCount("id")).toBe(1);
    expect(registry.getActiveMessageIds()).toEqual(["id"]);

    registry.removeHandler("id", handler);

    expect(registry.getHandlerCount("id")).toBe(0);
    expect(registry.getActiveMessageIds()).toEqual([]);
  });

  it("ignores a message with no registered handlers", () => {
    const shiny = fakeShiny();
    (window as any).Shiny = shiny;
    const registry = new ShinyMessageRegistry();
    registry.addHandler("known", vi.fn());

    expect(() => shiny.send("unknown", 1)).not.toThrow();
  });

  it("registers when Shiny arrives after the first attempt", () => {
    // initializeMessageRegistry() runs during shinyreact's one-time init, which
    // can happen before Shiny exists. It is a no-op then, with no retry — so
    // addHandler has to be able to install the dispatcher later.
    const registry = new ShinyMessageRegistry();
    initializeMessageRegistry();
    registry.addHandler("early", vi.fn());

    const shiny = fakeShiny();
    (window as any).Shiny = shiny;
    const handler = vi.fn();
    registry.addHandler("late", handler);

    expect(shiny.addCustomMessageHandler).toHaveBeenCalledTimes(1);

    shiny.send("late", "payload");
    expect(handler).toHaveBeenCalledWith("payload");
  });
});

describe("getMessageRegistry", () => {
  it("returns the module singleton when there is no Shiny, without attaching", () => {
    delete (window as any).Shiny;

    expect(getMessageRegistry()).toBe(getMessageRegistry());
  });

  it("attaches the registry to window.Shiny on first use", () => {
    const shiny = fakeShiny();
    (window as any).Shiny = shiny;

    const registry = getMessageRegistry();

    expect(shiny.messageRegistry).toBe(registry);
  });

  it("adopts a registry another copy of the library already attached", async () => {
    // The page-scoped-not-module-scoped property this design exists for. Two
    // copies of the bundle can coexist today (the page entry points serve
    // shinyreact.js unless an npm-tier app passes `shinyreact_js="client"`,
    // #217), and each has its own module singleton.
    // Whoever attaches first owns the page; everyone else must adopt it, or
    // there would be two dispatchers competing for Shiny's single slot per
    // message type and one copy's handlers would go dead.
    const shiny = fakeShiny();
    (window as any).Shiny = shiny;
    const first = getMessageRegistry();
    const handler = vi.fn();
    first.addHandler("shared", handler);

    // A second copy of the library: fresh module state, same page.
    vi.resetModules();
    const second = await import("../message-registry");
    expect(second.getMessageRegistry()).toBe(first);

    // Still exactly one dispatcher, and the first copy's handler still fires.
    second.getMessageRegistry().addHandler("other", vi.fn());
    expect(shiny.addCustomMessageHandler).toHaveBeenCalledTimes(1);
    shiny.send("shared", 42);
    expect(handler).toHaveBeenCalledWith(42);
  });
});
