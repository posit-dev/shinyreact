import { describe, it, expect, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import React from "react";
import type { Spec } from "../spec";
import { registerComponents, _resetForTests } from "../registry";
import { ShinyreactRenderer } from "../renderer";

beforeEach(() => {
  _resetForTests();
});

describe("ShinyreactRenderer", () => {
  it("renders a tag node with translated props and text child", () => {
    const spec: Spec = {
      type: "tag",
      name: "div",
      props: { className: "hi" },
      children: [{ type: "text", value: "hello" }],
    };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe('<div class="hi">hello</div>');
  });

  it("recursively renders nested tag children", () => {
    const spec: Spec = {
      type: "tag",
      name: "div",
      props: {},
      children: [
        { type: "tag", name: "span", props: {}, children: [{ type: "text", value: "one" }] },
        { type: "tag", name: "span", props: {}, children: [{ type: "text", value: "two" }] },
      ],
    };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe("<div><span>one</span><span>two</span></div>");
  });

  it("renders a html node via dangerouslySetInnerHTML", () => {
    const spec: Spec = { type: "html", html: "<b>bold</b>" };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe("<span><b>bold</b></span>");
  });

  it("dispatches a react node to a registered component receiving { element, children }", () => {
    const Box = ({
      element,
      children,
    }: {
      element: { props: Record<string, unknown> };
      children: React.ReactNode;
    }) => <section data-label={element.props.label as string}>{children}</section>;
    registerComponents(null, { Box });

    const spec: Spec = {
      type: "react",
      name: "Box",
      props: { label: "outer" },
      children: [{ type: "tag", name: "span", props: {}, children: [{ type: "text", value: "inside" }] }],
    };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe('<section data-label="outer"><span>inside</span></section>');
  });

  it("throws on an unknown registered component name", () => {
    const spec: Spec = { type: "react", name: "Missing", props: {}, children: [] };
    expect(() => render(<ShinyreactRenderer spec={spec} />)).toThrow(/Missing/);
  });

  it("renders an array payload as sibling nodes", () => {
    const spec: Spec = [
      { type: "tag", name: "span", props: {}, children: [{ type: "text", value: "a" }] },
      { type: "tag", name: "span", props: {}, children: [{ type: "text", value: "b" }] },
    ];
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe("<span>a</span><span>b</span>");
  });

  it("honors an explicit key in props without rendering it as an attribute", () => {
    const spec: Spec = {
      type: "tag",
      name: "div",
      props: { key: "k1", className: "x" },
      children: [],
    };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe('<div class="x"></div>');
  });

  it("renders a react node nested inside a tag node", () => {
    const Badge = ({ element }: { element: { props: Record<string, unknown> } }) => (
      <em>{element.props.text as string}</em>
    );
    registerComponents(null, { Badge });

    const spec: Spec = {
      type: "tag",
      name: "div",
      props: { className: "wrap" },
      children: [{ type: "react", name: "Badge", props: { text: "hi" }, children: [] }],
    };
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe('<div class="wrap"><em>hi</em></div>');
  });

  it("renders mixed text and tag siblings in an array", () => {
    const spec: Spec = [
      { type: "text", value: "before " },
      { type: "tag", name: "b", props: {}, children: [{ type: "text", value: "bold" }] },
    ];
    const { container } = render(<ShinyreactRenderer spec={spec} />);
    expect(container.innerHTML).toBe("before <b>bold</b>");
  });
});
