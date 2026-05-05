import { describe, it, expect, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import React from "react";
import type { Spec } from "../spec";
import { registerComponents, _resetForTests } from "../registry";
import { ShinyjsonRenderer } from "../renderer";

// Tests in this file rely on a clean registry between cases.
beforeEach(() => {
  _resetForTests();
});

describe("ShinyjsonRenderer", () => {
  it("renders a single intrinsic element with text props", () => {
    const spec: Spec = {
      root: "a",
      elements: {
        a: { type: "div", props: { className: "hi", children: "hello" } },
      },
    };
    const { container } = render(<ShinyjsonRenderer spec={spec} />);
    expect(container.innerHTML).toBe('<div class="hi">hello</div>');
  });

  it("recursively renders intrinsic children referenced by id", () => {
    const spec: Spec = {
      root: "root",
      elements: {
        root: { type: "div", props: {}, children: ["c1", "c2"] },
        c1: { type: "span", props: { children: "one" } },
        c2: { type: "span", props: { children: "two" } },
      },
    };
    const { container } = render(<ShinyjsonRenderer spec={spec} />);
    expect(container.innerHTML).toBe(
      "<div><span>one</span><span>two</span></div>",
    );
  });

  it("dispatches to a registered component receiving { element, children }", () => {
    const Box = ({
      element,
      children,
    }: {
      element: { props: Record<string, unknown> };
      children: React.ReactNode;
    }) => (
      <section data-label={element.props.label as string}>{children}</section>
    );
    registerComponents(null, { Box });

    const spec: Spec = {
      root: "root",
      elements: {
        root: { type: "Box", props: { label: "outer" }, children: ["leaf"] },
        leaf: { type: "span", props: { children: "inside" } },
      },
    };
    const { container } = render(<ShinyjsonRenderer spec={spec} />);
    expect(container.innerHTML).toBe(
      '<section data-label="outer"><span>inside</span></section>',
    );
  });

  it("renders nothing when an id reference is missing", () => {
    const spec: Spec = {
      root: "root",
      elements: {
        root: { type: "div", props: {}, children: ["missing"] },
      },
    };
    const { container } = render(<ShinyjsonRenderer spec={spec} />);
    expect(container.innerHTML).toBe("<div></div>");
  });

  it("treats omitted children as an empty list", () => {
    const spec: Spec = {
      root: "root",
      elements: {
        root: { type: "div", props: { className: "x" } },
      },
    };
    const { container } = render(<ShinyjsonRenderer spec={spec} />);
    expect(container.innerHTML).toBe('<div class="x"></div>');
  });
});
