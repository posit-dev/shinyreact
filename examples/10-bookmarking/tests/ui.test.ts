/**
 * Pins the `(test)` leaves in `examples/10-bookmarking/FEATURES.md`.
 *
 * The restore mechanism itself is pinned by the package suites (see that
 * file's "Covered elsewhere"); what is example-specific is the three input
 * shapes and the per-click event counter.
 */
import { fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { mountExample, type MountedExample } from "../../testing/mount";

const wire = (id: string) => `${id}:shinyreact.default`;

describe("examples/10-bookmarking client", () => {
  let app: MountedExample;

  beforeEach(async () => {
    app = await mountExample("10-bookmarking");
  });
  afterEach(() => app.cleanup());

  it("renders without waiting for useShinyInitialized()", () => {
    // Unlike the other examples, this one never gates on initialization.
    expect(app.container.querySelector("h1")?.textContent).toBe("Bookmarking demo");
  });

  it("sends each input's declared default", async () => {
    await app.settleDebounce();
    expect(app.lastInput(wire("txt"))).toBe("");
    expect(app.lastInput(wire("num"))).toBe(0);
    expect(app.lastInput(wire("chk"))).toBe(false);
  });

  it("sends the number field as a number and the checkbox as a boolean", async () => {
    const text = app.container.querySelector<HTMLInputElement>('input[type="text"]')!;
    const num = app.container.querySelector<HTMLInputElement>('input[type="number"]')!;
    const chk = app.container.querySelector<HTMLInputElement>('input[type="checkbox"]')!;

    await app.flush(() => {
      fireEvent.change(text, { target: { value: "hello" } });
      fireEvent.change(num, { target: { value: "42" } });
      fireEvent.click(chk);
    });
    await app.settleDebounce();

    expect(app.lastInput(wire("txt"))).toBe("hello");
    expect(app.lastInput(wire("num"))).toBe(42);
    expect(app.lastInput(wire("chk"))).toBe(true);
  });

  it("gives every bookmark click a distinct, incrementing event value", async () => {
    const button = app.container.querySelector<HTMLButtonElement>(
      '[data-testid="bookmark-btn"]',
    )!;

    await app.flush(() => button.click());
    await app.settleDebounce(20);
    expect(app.lastInput(wire("bookmark_clicks"))).toBe(1);

    await app.flush(() => button.click());
    await app.settleDebounce(20);
    expect(app.lastInput(wire("bookmark_clicks"))).toBe(2);
  });

  it("shows the server echo in the output card", async () => {
    await app.setOutput("greeting", "text='hi' num=1 checked=yes");
    expect(app.container.querySelector(".output")?.textContent).toBe(
      "Server says: text='hi' num=1 checked=yes",
    );
  });
});
