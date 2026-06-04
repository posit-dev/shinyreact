import { describe, it, expect, beforeEach, afterEach } from "vitest";
import React from "react";
import { act } from "react";
import { _resetForTests, registerComponents } from "../registry";
import { seedInlineSpecs, installInlineSpecSeeding } from "../inline-spec";

// Opt into React's act() support for the raw `act` from "react" (Testing
// Library sets this for us in other suites; this one drives roots directly).
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
  true;

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

function setReadyState(state: DocumentReadyState): void {
  Object.defineProperty(document, "readyState", {
    configurable: true,
    get: () => state,
  });
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

describe("installInlineSpecSeeding (load-time seeding, #123)", () => {
  afterEach(() => {
    // installInlineSpecSeeding may leave `once` listeners pending when a test
    // fires only some of the events it listens for. Remove them so a stray
    // event in a later test can't seed across test boundaries.
    document.removeEventListener("DOMContentLoaded", seedInlineSpecs);
    window.removeEventListener("load", seedInlineSpecs);
    setReadyState("complete");
  });

  // Ingredient 1: a `defer`-loaded bundle runs at readyState === "interactive",
  // BEFORE sibling `defer` bundles (which register components) have executed.
  // Seeding must therefore wait, not fire immediately, or it renders against an
  // incomplete registry.
  it("defers seeding until DOMContentLoaded when the document is still loading (readyState 'interactive')", async () => {
    setReadyState("interactive");
    const div = mountStatic(
      JSON.stringify({
        type: "tag",
        name: "div",
        props: { className: "seeded" },
        children: [{ type: "text", value: "hi" }],
      }),
    );

    await act(async () => {
      installInlineSpecSeeding();
    });
    // Not seeded yet — a sibling bundle's components may not be registered. The
    // mount still holds only its source <script>, with nothing rendered.
    expect(div.querySelector("div.seeded")).toBeNull();

    await act(async () => {
      document.dispatchEvent(new Event("DOMContentLoaded"));
    });
    expect(div.querySelector("div.seeded")?.textContent).toBe("hi");
  });

  // Ingredients 2 + 3 combined (the headline race): a static mount references a
  // component registered by a SEPARATE bundle whose `defer` script runs after
  // ours. If we seed immediately we render against an empty registry, the
  // renderer throws, and the root is poisoned for good — the badge never
  // appears. Deferring to DOMContentLoaded lets the registration land first.
  it("renders a mount whose component registers after install but before DOMContentLoaded", async () => {
    setReadyState("interactive");
    const div = mountStatic(
      JSON.stringify({
        type: "react",
        name: "Badge",
        props: { text: "static-badge" },
        children: [],
      }),
    );

    await act(async () => {
      installInlineSpecSeeding();
    });

    // Simulate the sibling component bundle's `defer` script registering later.
    const Badge = ({ element }: { element: { props: Record<string, unknown> } }) =>
      React.createElement(
        "span",
        { "data-testid": "badge" },
        element.props.text as string,
      );
    registerComponents(null, { Badge });

    await act(async () => {
      document.dispatchEvent(new Event("DOMContentLoaded"));
    });

    expect(div.querySelector('[data-testid="badge"]')?.textContent).toBe(
      "static-badge",
    );
  });

  // Edge: a bundle injected after the page has fully loaded (readyState
  // "complete") must still seed — there is no future DOMContentLoaded to wait
  // for.
  it("seeds immediately when the document is already complete", async () => {
    setReadyState("complete");
    const div = mountStatic(
      JSON.stringify({
        type: "tag",
        name: "div",
        props: { className: "now" },
        children: [{ type: "text", value: "x" }],
      }),
    );

    await act(async () => {
      installInlineSpecSeeding();
    });
    expect(div.innerHTML).toBe('<div class="now">x</div>');
  });

  // Robustness: seeding listens for both DOMContentLoaded and load (a safety
  // net). Both firing must not double-render the mount — seedInlineSpecs is
  // idempotent via hasRoot.
  it("seeds exactly once even if both DOMContentLoaded and load fire", async () => {
    setReadyState("interactive");
    const div = mountStatic(
      JSON.stringify({
        type: "tag",
        name: "div",
        props: { className: "once" },
        children: [{ type: "text", value: "1" }],
      }),
    );

    await act(async () => {
      installInlineSpecSeeding();
    });
    await act(async () => {
      document.dispatchEvent(new Event("DOMContentLoaded"));
    });
    await act(async () => {
      window.dispatchEvent(new Event("load"));
    });

    expect(div.innerHTML).toBe('<div class="once">1</div>');
    expect(div.querySelectorAll("div").length).toBe(1);
  });
});
