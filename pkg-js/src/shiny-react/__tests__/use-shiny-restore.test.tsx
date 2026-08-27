/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, expect, it, afterEach, beforeEach, vi } from "vitest";

vi.mock("../get-shiny", () => ({
  getShiny: vi.fn(() => undefined),
}));

import { InputRegistry } from "../input-registry";
import { applyRestoredValues } from "../bookmark";
import {
  _resetConfigTagRequirementForTesting,
  requireShinyReactConfigTag,
} from "../config";
import * as React from "react";
import { act, cleanup, render } from "@testing-library/react";
import { _resetShinyReactInitializedForTesting, useShinyInput } from "../use-shiny";
import { getReactRegistry } from "../react-registry";

function freshWindow(): void {
  // jsdom provides window; clear any prior shinyreact state.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (globalThis as any).window = (globalThis as any).window || {};
  delete (globalThis as any).window.shinyreact;
  document.getElementById("shinyreact-config")?.remove();
}

/** Insert the `#shinyreact-config` tag the way the server emits it. */
function setConfigTag(payload: object): void {
  const el = document.createElement("script");
  el.type = "application/json";
  el.id = "shinyreact-config";
  el.textContent = JSON.stringify(payload).replace(/</g, "\\u003c");
  document.head.appendChild(el);
}

describe("applyRestoredValues", () => {
  beforeEach(() => {
    freshWindow();
  });

  it("seeds registry entries from the #shinyreact-config tag", () => {
    setConfigTag({ protocolVersion: "1.0", restore: { foo: "hello", num: 42 } });
    const registry = new InputRegistry();

    applyRestoredValues(registry);

    expect(registry.get<string>("foo")?.getValue()).toBe("hello");
    expect(registry.get<number>("num")?.getValue()).toBe(42);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": { foo: "hello", num: 42 },
    });
  });

  it("ignores a pre-set window.shinyreact._restore global (config tag is the only channel)", () => {
    (window as any).shinyreact = { _restore: { foo: "from-legacy" } };
    const registry = new InputRegistry();

    applyRestoredValues(registry);

    expect(registry.size()).toBe(0);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": {},
    });
  });

  it("still runs the protocol handshake when _restore is already applied", () => {
    // The handshake is a property of the page, not of the restore payload. A
    // pre-set (or forged) "-applied" sentinel must not be able to skip version
    // checking — that would make the sentinel a silent kill switch.
    setConfigTag({ protocolVersion: "99.0" });
    (window as any).shinyreact = {
      _restore: { "-applied": true, "-values": {} },
    };

    expect(() => applyRestoredValues(new InputRegistry())).toThrow(
      /protocol mismatch/,
    );
  });

  it("preserves the existing snapshot when already applied and the protocol matches", () => {
    setConfigTag({ protocolVersion: "1.0", restore: { foo: "new" } });
    (window as any).shinyreact = {
      _restore: { "-applied": true, "-values": { foo: "old" } },
    };
    const registry = new InputRegistry();

    applyRestoredValues(registry);

    expect(registry.size()).toBe(0);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": { foo: "old" },
    });
  });

  it("config tag without restore writes the empty sentinel", () => {
    setConfigTag({ protocolVersion: "1.0" });
    const registry = new InputRegistry();

    applyRestoredValues(registry);

    expect(registry.size()).toBe(0);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": {},
    });
  });

  it("strict mode (npm build): throws when the config tag is missing", () => {
    requireShinyReactConfigTag();
    try {
      const registry = new InputRegistry();
      expect(() => applyRestoredValues(registry)).toThrowError(
        /upgrade the shinyreact/i,
      );
    } finally {
      _resetConfigTagRequirementForTesting();
    }
  });

  it("throws on a protocol major-version mismatch, naming both versions", () => {
    setConfigTag({ protocolVersion: "999.0", restore: { foo: "hello" } });
    const registry = new InputRegistry();

    expect(() => applyRestoredValues(registry)).toThrowError(/999\.0/);
  });

  it("with no config tag, leaves registry empty and writes empty sentinel", () => {
    (window as any).shinyreact = {};
    const registry = new InputRegistry();

    applyRestoredValues(registry);

    expect(registry.size()).toBe(0);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": {},
    });
  });

  it("with no window.shinyreact at all, creates the namespace and writes sentinel", () => {
    const registry = new InputRegistry();
    applyRestoredValues(registry);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": {},
    });
  });

  it("re-running does not clobber the -values snapshot", () => {
    setConfigTag({ protocolVersion: "1.0", restore: { foo: "hello" } });
    const registry = new InputRegistry();

    applyRestoredValues(registry);
    const firstValues = (window as any).shinyreact._restore["-values"];
    applyRestoredValues(registry);
    const secondValues = (window as any).shinyreact._restore["-values"];

    expect(secondValues).toEqual(firstValues);
    expect(secondValues).toEqual({ foo: "hello" });
  });

  it("does not call shiny setInputValue (uses add, not setValue)", () => {
    setConfigTag({ protocolVersion: "1.0", restore: { foo: "hello" } });
    const registry = new InputRegistry();
    const entry = vi.spyOn(registry, "add");

    applyRestoredValues(registry);

    // We use add() so the value is stored without invoking
    // shinySetInputValueDebounced. The first useShinyInput mount will
    // re-broadcast through setValue() at the existing path.
    expect(entry).toHaveBeenCalledWith("foo", "hello");
  });

  it("drains pendingSubscribers when seeding via add()", () => {
    setConfigTag({ protocolVersion: "1.0", restore: { foo: "hello" } });
    const registry = new InputRegistry();
    const subscriber = vi.fn();
    // Subscribe before the producer adds — should queue in pendingSubscribers.
    const unsub = registry.subscribe<string>("foo", subscriber);

    applyRestoredValues(registry);

    expect(subscriber).toHaveBeenCalledWith("hello");
    unsub();
  });

  it("uses a null-prototype object for the -values snapshot to prevent prototype pollution", () => {
    // The config tag arrives through JSON.parse, which turns "__proto__" /
    // "constructor" into own data properties, not prototype setters. The
    // snapshot assignment side of applyRestoredValues must preserve that.
    setConfigTag({
      protocolVersion: "1.0",
      restore: JSON.parse('{"__proto__":"evil","constructor":"x","foo":"ok"}'),
    });
    const registry = new InputRegistry();

    applyRestoredValues(registry);

    const values = (window as any).shinyreact._restore["-values"];
    // Null prototype: Object.getPrototypeOf returns null.
    expect(Object.getPrototypeOf(values)).toBeNull();
    // The "__proto__" key landed as a real own property, did not become the prototype.
    expect(Object.prototype.hasOwnProperty.call(values, "__proto__")).toBe(true);
    expect(values["__proto__"]).toBe("evil");
    expect(values["constructor"]).toBe("x");
    expect(values["foo"]).toBe("ok");
    // Object.prototype was not polluted by this run.
    expect(({} as Record<string, unknown>).evil).toBeUndefined();
  });
});

// Force `useShinyInitialized` to flip to true synchronously for these tests.
vi.mock("../lifecycle-store", () => {
  let initialized = true;
  return {
    subscribeLifecycle: (cb: () => void) => {
      initialized = true;
      cb();
      return () => {};
    },
    getInitializedSnapshot: () => initialized,
    getBusySnapshot: () => false,
  };
});

function Probe({ id, defVal }: { id: string; defVal: string }) {
  const [v] = useShinyInput<string>(id, defVal);
  return <span data-testid="v">{v}</span>;
}

describe("useShinyInput + restore", () => {
  beforeEach(() => {
    freshWindow();
    // Reset the module-level shinyReactInitialized flag so each test re-runs
    // ensureShinyReactInitialized (and therefore applyRestoredValues).
    _resetShinyReactInitializedForTesting();
    // Reset the singleton react registry between tests.
    // Guard against the first run where the registry may not yet be initialized.
    try {
      const reg = getReactRegistry();
      Array.from(reg.inputs.keys()).forEach((k) => reg.inputs.remove(k));
    } catch {
      // Registry not yet initialized — nothing to clear.
    }
  });

  afterEach(() => {
    cleanup();
  });

  it("adopts a restored value as initial render value, ignoring defaultValue", () => {
    setConfigTag({ protocolVersion: "1.0", restore: { foo: "hello" } });

    let utils!: ReturnType<typeof render>;
    act(() => {
      utils = render(<Probe id="foo" defVal="default" />);
    });

    expect(utils.getByTestId("v").textContent).toBe("hello");
  });

  it("uses defaultValue when no restore data is present", () => {
    (window as any).shinyreact = {};

    let utils!: ReturnType<typeof render>;
    act(() => {
      utils = render(<Probe id="bar" defVal="default" />);
    });

    expect(utils.getByTestId("v").textContent).toBe("default");
  });

  it("namespaced ids: restore {'ns-foo': 'hello'} is adopted by useShinyInput('foo', _, {namespace:'ns'})", () => {
    setConfigTag({ protocolVersion: "1.0", restore: { "ns-foo": "hello" } });

    function NsProbe() {
      const [v] = useShinyInput<string>("foo", "default", { namespace: "ns" });
      return <span data-testid="v">{v}</span>;
    }

    let utils!: ReturnType<typeof render>;
    act(() => {
      utils = render(<NsProbe />);
    });

    expect(utils.getByTestId("v").textContent).toBe("hello");
  });
});
