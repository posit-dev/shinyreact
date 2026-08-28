/** Pins the `(test)` leaves in `examples/08-input-handler/FEATURES.md`. */
import { fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { mountExample, type MountedExample } from "../../testing/mount";

const NOW_MS = 1_756_000_000_000; // 2025-08-24T02:26:40Z

describe("examples/08-input-handler client", () => {
  let app: MountedExample;

  beforeEach(async () => {
    vi.setSystemTime(NOW_MS);
    app = await mountExample("08-input-handler");
  });
  afterEach(() => {
    app.cleanup();
    vi.useRealTimers();
  });

  it("routes the value through the shiny.datetime handler, not shinyreact's", async () => {
    await app.settleDebounce(10);
    const wireIds = app.inputCalls.map((c) => c.wireId);

    expect(wireIds).toContain("when:shiny.datetime");
    expect(wireIds).not.toContain("when:shinyreact.default");
  });

  it("defaults to unix seconds, not milliseconds", async () => {
    await app.settleDebounce(10);
    expect(app.lastInput("when:shiny.datetime")).toBe(Math.floor(NOW_MS / 1000));

    const field = app.container.querySelector<HTMLInputElement>("input")!;
    expect(field.type).toBe("number");
    expect(field.value).toBe(String(Math.floor(NOW_MS / 1000)));
  });

  it("sends a number, not the field's string, on every keystroke", async () => {
    const field = app.container.querySelector<HTMLInputElement>("input")!;

    await app.flush(() =>
      fireEvent.change(field, { target: { value: "1000000000" } }),
    );
    await app.settleDebounce(10);

    expect(app.lastInput("when:shiny.datetime")).toBe(1000000000);
  });

  it("clearing the field sends the unix epoch, because Number('') is 0", async () => {
    const field = app.container.querySelector<HTMLInputElement>("input")!;

    await app.flush(() => fireEvent.change(field, { target: { value: "" } }));
    await app.settleDebounce(10);

    expect(app.lastInput("when:shiny.datetime")).toBe(0);
  });

  it("shows an ellipsis until the server echoes back", async () => {
    expect(app.container.querySelector(".echo")?.textContent).toBe("Server saw: …");

    await app.setOutput("when_info", "datetime → datetime.datetime(2025, 8, 24)");
    expect(app.container.querySelector(".echo")?.textContent).toBe(
      "Server saw: datetime → datetime.datetime(2025, 8, 24)",
    );
  });
});
