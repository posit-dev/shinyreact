/* eslint-disable @typescript-eslint/no-explicit-any */
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

let mockShiny: any = undefined;
vi.mock("../get-shiny", () => ({
  getShiny: () => mockShiny,
}));

import { __resetLifecycleStoreForTests } from "../lifecycle-store";
import { useShinyBusy, useShinyConnected } from "../use-shiny";

// A stand-in for the page's jQuery with the one property that matters here:
// `trigger()` calls jQuery handlers only. Real jQuery does the same for custom
// events, which is why Shiny's `$(document).trigger("shiny:disconnected")`
// never reaches an `addEventListener()` listener (#328).
function installFakeJQuery() {
  const handlers = new Map<string, Set<() => void>>();
  const $doc = {
    on(type: string, fn: () => void) {
      if (!handlers.has(type)) handlers.set(type, new Set());
      handlers.get(type)!.add(fn);
    },
    off(type: string, fn: () => void) {
      handlers.get(type)?.delete(fn);
    },
  };
  (window as any).jQuery = () => $doc;
  return {
    trigger: (type: string) =>
      act(() => handlers.get(type)?.forEach((fn) => fn())),
    count: (type: string) => handlers.get(type)?.size ?? 0,
  };
}

beforeEach(() => {
  mockShiny = undefined;
  __resetLifecycleStoreForTests();
});

afterEach(() => {
  __resetLifecycleStoreForTests();
  delete (window as any).jQuery;
});

describe("useShinyConnected", () => {
  it("is false before the socket opens", () => {
    const { result } = renderHook(() => useShinyConnected());
    expect(result.current).toBe(false);
  });

  it("follows connect, disconnect, and reconnect", () => {
    const { result } = renderHook(() => useShinyConnected());

    act(() => {
      document.dispatchEvent(new Event("shiny:connected"));
    });
    expect(result.current).toBe(true);

    act(() => {
      document.dispatchEvent(new Event("shiny:disconnected"));
    });
    expect(result.current).toBe(false);

    act(() => {
      document.dispatchEvent(new Event("shiny:connected"));
    });
    expect(result.current).toBe(true);
  });

  it("seeds true when the socket is already open at first mount", () => {
    mockShiny = {
      initializedPromise: new Promise(() => {}),
      shinyapp: { isConnected: () => true },
    };
    const { result } = renderHook(() => useShinyConnected());
    expect(result.current).toBe(true);
  });
});

describe("lifecycle events fired through jQuery (#328)", () => {
  it("useShinyConnected sees a jQuery-only shiny:disconnected", () => {
    const $ = installFakeJQuery();
    const { result } = renderHook(() => useShinyConnected());

    $.trigger("shiny:connected");
    expect(result.current).toBe(true);
    $.trigger("shiny:disconnected");
    expect(result.current).toBe(false);
  });

  it("useShinyBusy sees jQuery-only shiny:busy / shiny:idle", () => {
    const $ = installFakeJQuery();
    const { result } = renderHook(() => useShinyBusy());

    $.trigger("shiny:busy");
    expect(result.current).toBe(true);
    $.trigger("shiny:idle");
    expect(result.current).toBe(false);
  });

  it("detaches its jQuery handlers on reset", () => {
    const $ = installFakeJQuery();
    renderHook(() => useShinyConnected());
    expect($.count("shiny:disconnected")).toBe(1);

    __resetLifecycleStoreForTests();
    expect($.count("shiny:disconnected")).toBe(0);
  });
});

describe("Shiny present without jQuery", () => {
  it("warns, since native listeners never hear Shiny's events", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    mockShiny = { initializedPromise: new Promise(() => {}) };
    renderHook(() => useShinyConnected());
    expect(warn).toHaveBeenCalledWith(
      expect.stringContaining("window.jQuery is not"),
    );
    warn.mockRestore();
  });

  it("stays quiet when jQuery is there", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    installFakeJQuery();
    mockShiny = { initializedPromise: new Promise(() => {}) };
    renderHook(() => useShinyConnected());
    expect(warn).not.toHaveBeenCalled();
    warn.mockRestore();
  });
});
