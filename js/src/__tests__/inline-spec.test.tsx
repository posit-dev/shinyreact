import { describe, it, expect, beforeEach } from "vitest";
import { act } from "react";
import { _resetForTests } from "../registry";
import { seedInlineSpecs } from "../inline-spec";

beforeEach(() => {
  _resetForTests();
  document.body.innerHTML = "";
});

function mountStatic(specJson: string): HTMLElement {
  const div = document.createElement("div");
  div.className = "shinyreact-static";
  const script = document.createElement("script");
  script.type = "application/json";
  script.textContent = specJson;
  div.appendChild(script);
  document.body.appendChild(div);
  return div;
}

describe("seedInlineSpecs", () => {
  it("renders the inline spec into its containing static mount", async () => {
    const div = mountStatic(
      JSON.stringify({
        type: "tag",
        name: "div",
        props: { className: "seeded" },
        children: [{ type: "text", value: "hi" }],
      }),
    );
    await act(async () => {
      seedInlineSpecs();
    });
    expect(div.innerHTML).toBe('<div class="seeded">hi</div>');
  });

  it("ignores a static mount with no child JSON script", () => {
    const div = document.createElement("div");
    div.className = "shinyreact-static";
    document.body.appendChild(div);
    expect(() => seedInlineSpecs()).not.toThrow();
  });

  it("does not re-render a mount that already has a root", async () => {
    mountStatic(JSON.stringify({ type: "text", value: "first" }));
    await act(async () => {
      seedInlineSpecs();
    });
    expect(() => seedInlineSpecs()).not.toThrow();
  });
});
