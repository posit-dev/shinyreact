/* eslint-disable @typescript-eslint/no-explicit-any */
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  initializeMessageRegistry,
  ShinyMessageRegistry,
} from "../message-registry";

type Dispatcher = (msg: { id: string; data: unknown }) => void;

/** A minimal `window.Shiny` that records the custom-message dispatcher. */
function fakeShiny() {
  const handlers = new Map<string, Dispatcher>();
  return {
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

  it("registers when Shiny arrives after the first attempt, and publishes itself", () => {
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
    expect((window as any).Shiny.messageRegistry).toBe(registry);

    shiny.send("late", "payload");
    expect(handler).toHaveBeenCalledWith("payload");
  });
});
