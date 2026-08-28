/** Pins the `(test)` leaves in `examples/05-temperature/FEATURES.md`. */
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { mountExample, type MountedExample } from "../../testing/mount";

const CELSIUS = "celsius:shinyreact.default";

function sliders(app: MountedExample) {
  const [c, f] = app.container.querySelectorAll<HTMLInputElement>(".thermo-slider");
  return { c, f };
}

function setSlider(app: MountedExample, el: HTMLInputElement, value: number) {
  return app.flush(() => {
    el.value = String(value);
    el.dispatchEvent(new Event("input", { bubbles: true }));
  });
}

describe("examples/05-temperature client", () => {
  let app: MountedExample;

  beforeEach(async () => {
    app = await mountExample("05-temperature");
  });
  afterEach(() => app.cleanup());

  it("starts at 20 °C and derives 68 °F on the client", async () => {
    expect(app.container.querySelector(".temp-reading")?.textContent).toBe(
      "20°C = 68°F",
    );
    await app.settleDebounce(10);
    expect(app.lastInput(CELSIUS)).toBe(20);
  });

  it("gives the two sliders the same physical range", () => {
    const { c, f } = sliders(app);
    expect([c.min, c.max]).toEqual(["-40", "60"]);
    expect([f.min, f.max]).toEqual(["-40", "140"]);
  });

  it("labels and colors the zone from the same thresholds the server uses", async () => {
    const badge = () => app.container.querySelector<HTMLElement>(".temp-badge")!;
    const { c } = sliders(app);

    for (const [value, label, color] of [
      [0, "Freezing", "rgb(13, 202, 240)"],
      [1, "Cold", "rgb(13, 110, 253)"],
      [15, "Cold", "rgb(13, 110, 253)"],
      [16, "Comfortable", "rgb(25, 135, 84)"],
      [30, "Comfortable", "rgb(25, 135, 84)"],
      [31, "Hot", "rgb(220, 53, 69)"],
    ] as const) {
      await setSlider(app, c, value);
      expect(badge().textContent).toBe(label);
      expect(badge().style.backgroundColor).toBe(color);
    }
  });

  it("only Celsius is stored — the °F slider writes back through fToC", async () => {
    const { f } = sliders(app);

    await setSlider(app, f, 100);
    await app.settleDebounce(10);
    // fToC(100) = round(68 * 5/9) = 38
    expect(app.lastInput(CELSIUS)).toBe(38);
    expect(app.container.querySelector(".temp-reading")?.textContent).toBe(
      "38°C = 100°F",
    );
  });

  it("snaps back when a °F position has no exact Celsius twin", async () => {
    const { f } = sliders(app);

    // fToC(69) = round(37 * 5/9) = 21, and cToF(21) = 70.
    await setSlider(app, f, 69);
    await app.settleDebounce(10);
    expect(app.lastInput(CELSIUS)).toBe(21);
    expect(app.container.querySelector(".temp-reading")?.textContent).toBe(
      "21°C = 70°F",
    );
  });

  it("shows the server echo only once the display output arrives", async () => {
    expect(app.container.querySelector(".server-echo")).toBeNull();

    await app.setOutput("display", {
      celsius: 20,
      fahrenheit: 68.0,
      zone: "Comfortable",
    });

    expect(app.container.querySelector(".server-echo")?.textContent).toBe(
      "Server: 20°C → 68°F (Comfortable)",
    );
  });
});
