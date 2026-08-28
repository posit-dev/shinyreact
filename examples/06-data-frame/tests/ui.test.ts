/**
 * Pins the `(test)` leaves in `examples/06-data-frame/FEATURES.md`.
 *
 * This example exists to prove one thing: the element a traditional Shiny
 * binding attaches to is created by the *client*, with no server-side
 * `ui.output_data_frame()` placeholder. What the binding then draws into it is
 * Shiny's business, and the fake Shiny here runs no bindings — so this asserts
 * the host element's shape, which is the whole contract the example owns.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { mountExample, type MountedExample } from "../../testing/mount";

describe("examples/06-data-frame client", () => {
  let app: MountedExample;

  beforeEach(async () => {
    app = await mountExample("06-data-frame");
  });
  afterEach(() => app.cleanup());

  it("hosts the data frame in a <shiny-data-frame> the client creates", () => {
    const el = app.container.querySelector("#my_table")!;
    expect(el.tagName.toLowerCase()).toBe("shiny-data-frame");
    expect(el.className).toBe("");
  });

  it("renders the row-count slider as a 1-20 range input", async () => {
    const slider = app.container.querySelector<HTMLInputElement>("#row-count")!;
    expect(slider.type).toBe("range");
    expect([slider.min, slider.max, slider.value]).toEqual(["1", "20", "5"]);

    await app.settleDebounce();
    expect(app.lastInput("row_count:shinyreact.default")).toBe(5);
  });
});
