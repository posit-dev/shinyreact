/**
 * Pins the `(test)` leaves in `examples/07-plotly/FEATURES.md`.
 *
 * One client, two servers: the host element carries both shinywidgets' and
 * htmlwidgets' selectors, and no server declares a placeholder for it. The
 * fake Shiny here runs no bindings, so what is testable — and what the example
 * owns — is that host element's shape.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { mountExample, type MountedExample } from "../../testing/mount";

describe("examples/07-plotly client", () => {
  let app: MountedExample;

  beforeEach(async () => {
    app = await mountExample("07-plotly");
  });
  afterEach(() => app.cleanup());

  it("hosts the widget in one div carrying both bindings' selectors", () => {
    const el = app.container.querySelector<HTMLElement>("#scatter")!;
    expect(el.tagName).toBe("DIV");
    // Python's shinywidgets binding …
    expect(el.classList.contains("shiny-ipywidget-output")).toBe(true);
    // … and R's htmlwidgets/plotly binding, on the same element.
    expect(el.classList.contains("html-widget-output")).toBe(true);
    expect(el.classList.contains("plotly")).toBe(true);
    expect(el.classList.contains("shiny-report-size")).toBe(true);
  });

  it("renders the point-count slider as a 10-500 range input", async () => {
    const slider = app.container.querySelector<HTMLInputElement>("#num-points")!;
    expect(slider.type).toBe("range");
    expect([slider.min, slider.max, slider.value]).toEqual(["10", "500", "50"]);

    await app.settleDebounce();
    expect(app.lastInput("num_points:shinyreact.default")).toBe(50);
  });
});
