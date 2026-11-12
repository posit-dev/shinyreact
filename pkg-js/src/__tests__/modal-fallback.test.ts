/* eslint-disable @typescript-eslint/no-explicit-any */
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  installModalFallback,
  MODAL_FALLBACK_MESSAGE,
} from "../modal-fallback";

afterEach(() => {
  delete (window as any).jQuery;
  vi.restoreAllMocks();
});

describe("installModalFallback (#326)", () => {
  it("fills an empty jQuery.fn.modal with a function that explains", () => {
    (window as any).jQuery = { fn: {} };
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    installModalFallback();

    // Shiny's modal script: `$('#shiny-modal').modal().focus()`.
    const $el = { focus: vi.fn() };
    const out = (window as any).jQuery.fn.modal.call($el);

    expect(out).toBe($el);
    expect(error).toHaveBeenCalledWith(MODAL_FALLBACK_MESSAGE);
  });

  it("leaves Bootstrap's modal alone", () => {
    const bootstrapModal = () => {};
    (window as any).jQuery = { fn: { modal: bootstrapModal } };
    installModalFallback();
    expect((window as any).jQuery.fn.modal).toBe(bootstrapModal);
  });

  it("does nothing without jQuery", () => {
    expect(() => installModalFallback()).not.toThrow();
    expect((window as any).jQuery).toBeUndefined();
  });

  it("names both bookmark fixes", () => {
    expect(MODAL_FALLBACK_MESSAGE).toContain("updateQueryString(url)");
    expect(MODAL_FALLBACK_MESSAGE).toContain(
      "session.bookmark.on_bookmarked(session.bookmark.update_query_string)",
    );
  });
});
