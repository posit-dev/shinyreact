import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

// Mock getShiny before importing the module under test
const mockSetInputValue = vi.fn();
vi.mock("../get-shiny", () => ({
  getShiny: vi.fn(() => undefined),
}));

import { InputRegistry, InputRegistryEntry } from "../input-registry";
import { getShiny } from "../get-shiny";
import { MISSING } from "../missing";

describe("InputRegistryEntry", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("stores initial value", () => {
    const entry = new InputRegistryEntry("test", 42);
    expect(entry.getValue()).toBe(42);
  });

  it("setValue updates value and notifies setState functions", () => {
    const entry = new InputRegistryEntry("test", 0);
    const setStateFn = vi.fn();
    entry.addUseStateSetValueFn(setStateFn);

    entry.setValue(5);
    expect(entry.getValue()).toBe(5);
    expect(setStateFn).toHaveBeenCalledWith(5);
  });

  it("removeUseStateSetValueFn stops notifications", () => {
    const entry = new InputRegistryEntry("test", 0);
    const setStateFn = vi.fn();
    entry.addUseStateSetValueFn(setStateFn);
    entry.removeUseStateSetValueFn(setStateFn);

    entry.setValue(5);
    expect(setStateFn).not.toHaveBeenCalled();
  });

  it("does not throw when Shiny is unavailable", () => {
    vi.mocked(getShiny).mockReturnValue(undefined);
    const entry = new InputRegistryEntry("test", 0);

    // setValue triggers debounced setShinyInputValue — should not throw
    entry.setValue(1);
    expect(() => vi.advanceTimersByTime(200)).not.toThrow();
  });

  it("does not throw when Shiny exists but setInputValue is undefined", () => {
    // Simulates Shiny partially initialized — object exists but method missing
    vi.mocked(getShiny).mockReturnValue({} as any);
    const entry = new InputRegistryEntry("test", 0);

    entry.setValue(1);
    // The ?. operator should prevent a throw here
    expect(() => vi.advanceTimersByTime(200)).not.toThrow();
  });

  it("calls Shiny.setInputValue when Shiny is available", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("test", 0);

    entry.setValue(42);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "test:shinyreact.default",
      42,
      expect.objectContaining({ debounceMs: 100 }),
    );
  });

  it("setValue accepts a functional updater, resolved against the current value", () => {
    const entry = new InputRegistryEntry("test", 1);
    const setStateFn = vi.fn();
    entry.addUseStateSetValueFn(setStateFn);

    entry.setValue((n) => n + 1);

    expect(entry.getValue()).toBe(2);
    // React state is notified with the resolved value, never the function itself.
    expect(setStateFn).toHaveBeenCalledWith(2);
  });

  it("functional updaters chain across successive calls", () => {
    const entry = new InputRegistryEntry("test", 0);
    entry.setValue((n) => n + 1);
    entry.setValue((n) => n + 1);
    entry.setValue((n) => n * 10);
    expect(entry.getValue()).toBe(20);
  });

  it("sends the resolved value (not the function) to Shiny.setInputValue", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("test", 5);

    entry.setValue((n) => n + 10);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "test:shinyreact.default",
      15,
      expect.objectContaining({ debounceMs: 100 }),
    );
  });

  it("MISSING value updates React state but does not call setInputValue", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("test", MISSING);
    const setStateFn = vi.fn();
    entry.addUseStateSetValueFn(setStateFn);

    entry.setValue(MISSING);
    vi.advanceTimersByTime(200);

    expect(setStateFn).toHaveBeenCalledWith(MISSING);
    expect(mockSetInputValue).not.toHaveBeenCalled();
  });

  it("real value after MISSING calls setInputValue", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("test", MISSING);
    const setStateFn = vi.fn();
    entry.addUseStateSetValueFn(setStateFn);

    // First set MISSING — should not send
    entry.setValue(MISSING);
    vi.advanceTimersByTime(200);
    expect(mockSetInputValue).not.toHaveBeenCalled();

    // Then set a real value — should send
    entry.setValue(300 as any);
    vi.advanceTimersByTime(200);
    expect(mockSetInputValue).toHaveBeenCalledWith(
      "test:shinyreact.default",
      300,
      expect.objectContaining({ debounceMs: 100 }),
    );
  });

  it("null value (without MISSING) still calls setInputValue", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("test", null);

    entry.setValue(null);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "test:shinyreact.default",
      null,
      expect.objectContaining({ debounceMs: 100 }),
    );
  });

  it("isEmpty returns true when no setState functions registered", () => {
    const entry = new InputRegistryEntry("test", 0);
    expect(entry.isEmpty()).toBe(true);
  });

  it("isEmpty returns false when setState functions are registered", () => {
    const entry = new InputRegistryEntry("test", 0);
    entry.addUseStateSetValueFn(vi.fn());
    expect(entry.isEmpty()).toBe(false);
  });

  it("type defaults to undefined and the wire id has the shinyreact.default suffix", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);

    entry.setValue(1);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:shinyreact.default",
      1,
      expect.objectContaining({ debounceMs: 100 }),
    );
  });

  it("updateType(string) causes wire id to be 'id:type'", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);
    entry.updateType("shiny.datetime");

    entry.setValue(1);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:shiny.datetime",
      1,
      expect.objectContaining({ debounceMs: 100 }),
    );
  });

  it("updateType is set-once: same value is a no-op", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);
    entry.updateType("X");
    entry.updateType("X");

    entry.setValue(1);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:X",
      1,
      expect.anything(),
    );
  });

  it("updateType after a string: omission (undefined) is a no-op", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);
    entry.updateType("X");
    entry.updateType(undefined);

    entry.setValue(1);
    vi.advanceTimersByTime(200);

    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:X",
      1,
      expect.anything(),
    );
  });

  it("updateType after a string: conflicting string throws and entry stays unchanged", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);
    entry.updateType("X");

    expect(() => entry.updateType("Y")).toThrow(/already registered with type="X"/);

    entry.setValue(1);
    vi.advanceTimersByTime(200);
    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:X",
      1,
      expect.anything(),
    );
  });

  it("updateType after undefined finalizes 'no type'; later string throws", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const entry = new InputRegistryEntry("foo", 0);
    entry.updateType(undefined);

    expect(() => entry.updateType("X")).toThrow(/already registered with type=undefined/);

    entry.setValue(1);
    vi.advanceTimersByTime(200);
    expect(mockSetInputValue).toHaveBeenCalledWith(
      "foo:shinyreact.default",
      1,
      expect.anything(),
    );
  });
});

describe("InputRegistry", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("add creates an entry and get retrieves it", () => {
    const registry = new InputRegistry();
    const entry = registry.add("count", 0);
    expect(entry.getValue()).toBe(0);
    expect(registry.get("count")).toBe(entry);
  });

  it("add throws if entry already exists", () => {
    const registry = new InputRegistry();
    registry.add("count", 0);
    expect(() => registry.add("count", 1)).toThrow("Input count already exists");
  });

  it("getOrCreate returns existing entry", () => {
    const registry = new InputRegistry();
    const entry = registry.add("count", 0);
    const same = registry.getOrCreate("count", 99);
    expect(same).toBe(entry);
    expect(same.getValue()).toBe(0); // original value, not 99
  });

  it("getOrCreate creates new entry if missing", () => {
    const registry = new InputRegistry();
    const entry = registry.getOrCreate("count", 42);
    expect(entry.getValue()).toBe(42);
    expect(registry.has("count")).toBe(true);
  });

  it("remove cancels pending debounced calls", () => {
    vi.mocked(getShiny).mockReturnValue({
      setInputValue: mockSetInputValue,
    } as any);
    const registry = new InputRegistry();
    const entry = registry.add("count", 0);

    // Trigger a setValue which schedules a debounced Shiny update
    entry.setValue(5);
    // Remove before debounce fires
    registry.remove("count");

    // Advance past the debounce delay
    vi.advanceTimersByTime(200);

    // setInputValue should NOT have been called — debounce was cancelled
    expect(mockSetInputValue).not.toHaveBeenCalled();
  });

  it("remove returns false for non-existent entry", () => {
    const registry = new InputRegistry();
    expect(registry.remove("nonexistent")).toBe(false);
  });

  it("size tracks entry count", () => {
    const registry = new InputRegistry();
    expect(registry.size()).toBe(0);
    registry.add("a", 1);
    registry.add("b", 2);
    expect(registry.size()).toBe(2);
    registry.remove("a");
    expect(registry.size()).toBe(1);
  });
});

describe("InputRegistry.subscribe (read-only consumer)", () => {
  it("attaches subscriber immediately when entry exists", () => {
    const registry = new InputRegistry();
    registry.add("foo", 7);
    const setFn = vi.fn();

    const dispose = registry.subscribe("foo", setFn);

    // Initial sync: subscriber receives current value on attach
    expect(setFn).toHaveBeenCalledWith(7);

    // Subsequent producer updates flow to subscriber
    registry.get("foo")!.setValue(8);
    expect(setFn).toHaveBeenLastCalledWith(8);

    dispose();
  });

  it("queues subscriber when entry does not yet exist, then drains on add()", () => {
    const registry = new InputRegistry();
    const setFn = vi.fn();

    const dispose = registry.subscribe("foo", setFn);
    expect(setFn).not.toHaveBeenCalled();

    // Producer arrives later
    registry.add("foo", 42);
    expect(setFn).toHaveBeenCalledWith(42);

    registry.get("foo")!.setValue(43);
    expect(setFn).toHaveBeenLastCalledWith(43);

    dispose();
  });

  it("dispose() removes pending subscriber if entry was never created", () => {
    const registry = new InputRegistry();
    const setFn = vi.fn();
    const dispose = registry.subscribe("foo", setFn);
    dispose();

    registry.add("foo", 1);
    expect(setFn).not.toHaveBeenCalled();
  });

  it("dispose() removes attached subscriber from existing entry", () => {
    const registry = new InputRegistry();
    registry.add("foo", 1);
    const setFn = vi.fn();
    const dispose = registry.subscribe("foo", setFn);
    setFn.mockClear();

    dispose();

    registry.get("foo")!.setValue(2);
    expect(setFn).not.toHaveBeenCalled();
  });

  it("dispose() is idempotent (safe to call twice)", () => {
    const registry = new InputRegistry();
    registry.add("foo", 1);
    const setFn = vi.fn();
    const dispose = registry.subscribe("foo", setFn);
    setFn.mockClear();

    dispose();
    expect(() => dispose()).not.toThrow();

    registry.get("foo")!.setValue(2);
    expect(setFn).not.toHaveBeenCalled();
  });

  it("multiple subscribers on the same pending id all receive the value, and dispose is independent", () => {
    const registry = new InputRegistry();
    const setFn1 = vi.fn();
    const setFn2 = vi.fn();
    const dispose1 = registry.subscribe("foo", setFn1);
    const dispose2 = registry.subscribe("foo", setFn2);

    registry.add("foo", 99);
    expect(setFn1).toHaveBeenCalledWith(99);
    expect(setFn2).toHaveBeenCalledWith(99);

    dispose1();
    registry.get("foo")!.setValue(100);
    expect(setFn1).not.toHaveBeenCalledWith(100);
    expect(setFn2).toHaveBeenCalledWith(100);

    dispose2();
  });
});
