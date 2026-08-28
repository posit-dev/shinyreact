/**
 * Pins the `(test)` leaves in `examples/01-hello/FEATURES.md` that live on the
 * client. The histogram *data* claims are pinned server-side, in Python
 * (`tests/test_faithful.py`) and R (`tests/test-histogram.R`) next to it —
 * the golden counts below
 * are the same vector all three assert.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { mountExample, type MountedExample } from "../../testing/mount";

// bins = 9 over the 272 Old Faithful waiting times. Identical in R's hist()
// and faithful.py's binner; see examples/01-hello/FEATURES.md § Server.
const COUNTS_9 = [16, 37, 30, 16, 14, 57, 67, 29, 6];
const BREAKS_9 = [43, 48.889, 54.778, 60.667, 66.556, 72.444, 78.333, 84.222, 90.111, 96];

describe("examples/01-hello client", () => {
  let app: MountedExample;

  beforeEach(async () => {
    app = await mountExample("01-hello");
  });
  afterEach(() => app.cleanup());

  it("shows the Loading placeholder until dist_data arrives", () => {
    const placeholder = app.container.querySelector(".placeholder");
    expect(placeholder?.textContent).toBe("Loading…");
    expect(app.container.querySelector("svg")).toBeNull();
  });

  it("sends bins=30 as the initial input value, after the default debounce", async () => {
    // `bins` sets no debounceMs, so the hook's 100 ms default applies and
    // nothing is on the wire yet.
    expect(app.inputCalls).toEqual([]);

    await app.settleDebounce();
    expect(app.lastInput("bins:shinyreact.default")).toBe(30);
  });

  it("renders the bins slider as a 1-50 range input", () => {
    const slider = app.container.querySelector<HTMLInputElement>("#bins");
    expect(slider?.type).toBe("range");
    expect(slider?.min).toBe("1");
    expect(slider?.max).toBe("50");
    expect(slider?.value).toBe("30");
  });

  it("draws one bar per count once dist_data arrives", async () => {
    await app.setOutput("dist_data", { breaks: BREAKS_9, counts: COUNTS_9 });

    const bars = app.container.querySelectorAll("rect");
    expect(bars.length).toBe(9);
    expect([...bars].every((b) => b.getAttribute("fill") === "#447099")).toBe(true);
    expect(app.container.querySelector(".placeholder")).toBeNull();
  });

  it("labels the chart with the bin count for screen readers", async () => {
    await app.setOutput("dist_data", { breaks: BREAKS_9, counts: COUNTS_9 });

    const svg = app.container.querySelector("svg");
    expect(svg?.getAttribute("role")).toBe("img");
    expect(svg?.getAttribute("aria-label")).toBe(
      "Histogram of Old Faithful waiting times in 9 bins",
    );
  });

  it("bar heights are proportional to the counts", async () => {
    await app.setOutput("dist_data", { breaks: BREAKS_9, counts: COUNTS_9 });

    const heights = [...app.container.querySelectorAll("rect")].map((b) =>
      Number(b.getAttribute("height")),
    );
    // The tallest bar is the 67 and the shortest is the 6.
    expect(heights.indexOf(Math.max(...heights))).toBe(COUNTS_9.indexOf(67));
    expect(heights.indexOf(Math.min(...heights))).toBe(COUNTS_9.indexOf(6));
    expect(heights[COUNTS_9.indexOf(6)] / heights[COUNTS_9.indexOf(67)]).toBeCloseTo(
      6 / 67,
      5,
    );
  });

  it("renders the caption verbatim", async () => {
    await app.setOutput("dist_caption", "272 eruptions in 9 bins");
    expect(app.container.querySelector(".caption")?.textContent).toBe(
      "272 eruptions in 9 bins",
    );
  });

  it("dims the chart while recalculating instead of unmounting it", async () => {
    await app.setOutput("dist_data", { breaks: BREAKS_9, counts: COUNTS_9 });
    const svgBefore = app.container.querySelector("svg");

    await app.setRecalculating("dist_data", true);

    // Same SVG node — the chart was never torn down.
    expect(app.container.querySelector("svg")).toBe(svgBefore);
    expect(app.container.querySelector(".recalculating")).not.toBeNull();
    expect(app.container.querySelector(".placeholder")).toBeNull();

    await app.setRecalculating("dist_data", false);
    expect(app.container.querySelector(".recalculating")).toBeNull();
  });
});
