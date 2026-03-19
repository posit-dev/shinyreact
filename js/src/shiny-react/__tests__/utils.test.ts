import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { createDebouncedFn } from "../utils";

describe("createDebouncedFn", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("calls the function after the delay", () => {
    const fn = vi.fn();
    const debounced = createDebouncedFn(fn, 100);

    debounced("a");
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledWith("a");
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("resets timer on subsequent calls within delay", () => {
    const fn = vi.fn();
    const debounced = createDebouncedFn(fn, 100);

    debounced("a");
    vi.advanceTimersByTime(80);
    debounced("b");
    vi.advanceTimersByTime(80);
    // 160ms total, but only 80ms since last call — should not have fired yet
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(20);
    expect(fn).toHaveBeenCalledWith("b");
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("cancel() prevents pending invocation", () => {
    const fn = vi.fn();
    const debounced = createDebouncedFn(fn, 100);

    debounced("a");
    vi.advanceTimersByTime(50);
    debounced.cancel();

    vi.advanceTimersByTime(200);
    expect(fn).not.toHaveBeenCalled();
  });

  it("cancel() is safe to call when no timer is pending", () => {
    const fn = vi.fn();
    const debounced = createDebouncedFn(fn, 100);

    // Cancel with nothing pending — should not throw
    expect(() => debounced.cancel()).not.toThrow();
  });

  it("setDelay() changes the delay for subsequent calls", () => {
    const fn = vi.fn();
    const debounced = createDebouncedFn(fn, 100);

    debounced.setDelay(50);
    expect(debounced.getDelay()).toBe(50);

    debounced("a");
    vi.advanceTimersByTime(50);
    expect(fn).toHaveBeenCalledWith("a");
  });
});
