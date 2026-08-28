/** Pins the `(test)` leaves in `examples/02-columns/FEATURES.md`. */
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { mountExample, type MountedExample } from "../../testing/mount";

const DATA = {
  A: ["Apple", "Apricot"],
  B: ["Banana", "Blueberry"],
  C: ["Cherry", "Cranberry"],
};

const MOVE_ITEM = "move_item:shinyreact.default";

function columns(app: MountedExample): HTMLElement[] {
  return [...app.container.querySelectorAll("h4")].map(
    (h) => h.parentElement as HTMLElement,
  );
}

describe("examples/02-columns client", () => {
  let app: MountedExample;

  beforeEach(async () => {
    app = await mountExample("02-columns");
  });
  afterEach(() => app.cleanup());

  it("renders three columns from its own constant, not the server payload", async () => {
    // Before any data has arrived there are still three columns.
    expect(columns(app).map((c) => c.querySelector("h4")?.textContent)).toEqual([
      "Column A",
      "Column B",
      "Column C",
    ]);

    // A payload missing a column does not drop it or throw.
    await app.setOutput("column_data", { A: ["Apple"] });
    expect(columns(app).length).toBe(3);
  });

  it("renders (empty) for a column with no items", async () => {
    expect(columns(app)[0].textContent).toContain("(empty)");

    await app.setOutput("column_data", DATA);
    expect(columns(app)[0].textContent).not.toContain("(empty)");

    await app.setOutput("column_data", { ...DATA, B: [] });
    expect(columns(app)[1].textContent).toContain("(empty)");
  });

  it("omits ← in the first column and → in the last", async () => {
    await app.setOutput("column_data", DATA);
    const [a, b, c] = columns(app).map((col) =>
      [...col.querySelectorAll("button")].map((btn) => btn.textContent),
    );

    expect(a).toEqual(["→", "→"]);
    expect(b).toEqual(["←", "→", "←", "→"]);
    expect(c).toEqual(["←", "←"]);
  });

  it("sends {item, from, to} for the neighboring column on click", async () => {
    await app.setOutput("column_data", DATA);
    const banana = [...app.container.querySelectorAll("div")].find(
      (d) => d.firstElementChild?.textContent === "Banana",
    )!;
    const [left, right] = banana.querySelectorAll("button");

    await app.flush(() => left.click());
    await app.settleDebounce(20);
    expect(app.lastInput(MOVE_ITEM)).toEqual({
      item: "Banana",
      from: "B",
      to: "A",
    });

    await app.flush(() => right.click());
    await app.settleDebounce(20);
    expect(app.lastInput(MOVE_ITEM)).toEqual({
      item: "Banana",
      from: "B",
      to: "C",
    });
  });

  it("sends every click immediately (debounceMs: 0, priority event)", async () => {
    await app.setOutput("column_data", DATA);
    const before = app.inputCalls.length;
    const buttons = app.container.querySelectorAll("button");

    // 20 ms apart: far inside the 100 ms default debounce that would coalesce
    // them, and far outside the 0 ms this example asks for.
    await app.flush(() => buttons[0].click());
    await app.settleDebounce(20);
    await app.flush(() => buttons[1].click());
    await app.settleDebounce(20);

    // Two clicks, two messages — no debounce coalescing.
    expect(app.inputCalls.length - before).toBe(2);
    expect(app.inputCalls[app.inputCalls.length - 1].opts).toMatchObject({
      priority: "event",
    });
  });
});
