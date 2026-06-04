import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { act } from "react";
import { _resetForTests } from "../registry";
import {
  seedInlineSpecs,
  installInlineSpecSeeding,
  _stopMountObserverForTests,
} from "../inline-spec";

beforeEach(() => {
  _resetForTests();
  document.body.innerHTML = "";
});

afterEach(() => {
  _stopMountObserverForTests();
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

  it("seeds a static mount passed as the root itself (not just descendants)", async () => {
    const div = document.createElement("div");
    div.className = "shinyreact-static";
    const script = document.createElement("script");
    script.type = "application/json";
    script.textContent = JSON.stringify({
      type: "tag",
      name: "span",
      props: {},
      children: [{ type: "text", value: "self" }],
    });
    div.appendChild(script);
    // Not attached to the document: prove the mount itself is seeded, not via
    // a document-wide query.
    await act(async () => {
      seedInlineSpecs(div);
    });
    expect(div.innerHTML).toBe("<span>self</span>");
  });

  it("scopes seeding to the given root", async () => {
    const inside = mountStatic(JSON.stringify({ type: "text", value: "in" }));
    const outside = mountStatic(JSON.stringify({ type: "text", value: "out" }));
    const scope = document.createElement("div");
    scope.appendChild(inside);
    document.body.appendChild(scope);
    await act(async () => {
      seedInlineSpecs(scope);
    });
    // Seeded: React replaced the mount's children, so the JSON script is gone.
    expect(inside.textContent).toBe("in");
    expect(inside.querySelector("script")).toBeNull();
    // Untouched (not under scope): still holds its unrendered JSON script.
    expect(outside.querySelector("script")).not.toBeNull();
  });
});

describe("installInlineSpecSeeding (post-load observer)", () => {
  it("seeds a static mount inserted after install", async () => {
    installInlineSpecSeeding();

    const div = document.createElement("div");
    div.className = "shinyreact-static";
    const script = document.createElement("script");
    script.type = "application/json";
    script.textContent = JSON.stringify({ type: "text", value: "later" });
    div.appendChild(script);

    await act(async () => {
      document.body.appendChild(div);
      // Let the MutationObserver callback flush.
      await Promise.resolve();
    });

    expect(div.textContent).toBe("later");
  });

  it("seeds a static mount nested inside inserted content", async () => {
    installInlineSpecSeeding();

    const wrapper = document.createElement("div");
    wrapper.innerHTML =
      '<div class="shinyreact-static">' +
      '<script type="application/json">{"type":"text","value":"nested"}</script>' +
      "</div>";

    await act(async () => {
      document.body.appendChild(wrapper);
      await Promise.resolve();
    });

    expect(wrapper.querySelector(".shinyreact-static")?.textContent).toBe(
      "nested",
    );
  });
});
