import { render } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ShinyOutput } from "../shiny-output";

describe("ShinyOutput", () => {
  let mockBindAll: ReturnType<typeof vi.fn>;
  let mockUnbindAll: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockBindAll = vi.fn();
    mockUnbindAll = vi.fn();
    (window as any).Shiny = {
      bindAll: mockBindAll,
      unbindAll: mockUnbindAll,
    };
  });

  afterEach(() => {
    delete (window as any).Shiny;
  });

  it("renders the element with the given id and class", () => {
    const { container } = render(
      <ShinyOutput id="my_plot" className="plotly-output" />,
    );
    const el = container.querySelector("#my_plot");
    expect(el).not.toBeNull();
    expect(el?.classList.contains("plotly-output")).toBe(true);
    expect(el?.tagName).toBe("DIV");
  });

  it("renders a custom element when tagName is specified", () => {
    const { container } = render(
      <ShinyOutput id="my_table" tagName="shiny-data-frame" />,
    );
    const el = container.querySelector("#my_table");
    expect(el).not.toBeNull();
    expect(el?.tagName.toLowerCase()).toBe("shiny-data-frame");
  });

  it("renders without a wrapper element", () => {
    const { container } = render(
      <ShinyOutput id="my_plot" className="plotly-output" />,
    );
    const el = container.querySelector("#my_plot");
    expect(container.firstElementChild).toBe(el);
    expect(container.children.length).toBe(1);
  });

  it("preserves CSS layout for direct children (flexbox/grid)", () => {
    // The element must be a *direct* child of its parent for parent CSS
    // selectors like flex `gap`, `> *`, and grid layouts to apply.
    const { container } = render(
      <div style={{ display: "flex" }}>
        <ShinyOutput id="a" />
        <ShinyOutput id="b" />
      </div>,
    );
    const flex = container.firstElementChild!;
    expect(flex.children.length).toBe(2);
    expect(flex.children[0].id).toBe("a");
    expect(flex.children[1].id).toBe("b");
  });

  it("calls Shiny.bindAll on mount", () => {
    render(<ShinyOutput id="my_plot" className="plotly-output" />);
    expect(mockBindAll).toHaveBeenCalledTimes(1);
  });

  it("calls Shiny.unbindAll on unmount", () => {
    const { unmount } = render(
      <ShinyOutput id="my_plot" className="plotly-output" />,
    );
    unmount();
    expect(mockUnbindAll).toHaveBeenCalledTimes(1);
  });

  it("passes additional props to the element", () => {
    const { container } = render(
      <ShinyOutput
        id="my_plot"
        className="plotly-output"
        style={{ height: "400px" }}
        data-testid="plot-container"
      />,
    );
    const el = container.querySelector("#my_plot") as HTMLElement;
    expect(el?.style.height).toBe("400px");
    expect(el?.dataset.testid).toBe("plot-container");
  });

  it("is a no-op when window.Shiny is not available", () => {
    delete (window as any).Shiny;
    expect(() =>
      render(<ShinyOutput id="my_plot" className="plotly-output" />),
    ).not.toThrow();
  });

  it("binds with the parent as scope so descendants-only find() locates the element", () => {
    // Shiny's output bindings use `$(scope).find(selector)`, which excludes
    // `scope` itself. Binding the element directly would silently no-op for
    // non-custom-element outputs. The parent guarantees our output is a
    // descendant.
    const { container } = render(
      <div data-testid="parent">
        <ShinyOutput id="my_plot" className="plotly-output" />
      </div>,
    );
    const parent = container.querySelector("[data-testid='parent']");
    expect(mockBindAll).toHaveBeenCalledWith(parent);
  });

  it("unbinds only the element itself (includeSelf=true), not the whole parent", () => {
    // Calling unbindAll on the parent would clobber sibling outputs.
    // includeSelf=true scopes the unbind to just this element.
    const { container, unmount } = render(
      <ShinyOutput id="my_plot" className="plotly-output" />,
    );
    const el = container.querySelector("#my_plot");
    unmount();
    expect(mockUnbindAll).toHaveBeenCalledWith(el, true);
  });

  it("re-binds when id changes", () => {
    const { rerender } = render(<ShinyOutput id="first" />);
    expect(mockBindAll).toHaveBeenCalledTimes(1);
    expect(mockUnbindAll).toHaveBeenCalledTimes(0);

    rerender(<ShinyOutput id="second" />);
    expect(mockUnbindAll).toHaveBeenCalledTimes(1);
    expect(mockBindAll).toHaveBeenCalledTimes(2);
  });

  it("re-binds when tagName changes", () => {
    const { rerender } = render(<ShinyOutput id="my_plot" tagName="div" />);
    expect(mockBindAll).toHaveBeenCalledTimes(1);

    rerender(<ShinyOutput id="my_plot" tagName="shiny-data-frame" />);
    expect(mockUnbindAll).toHaveBeenCalledTimes(1);
    expect(mockBindAll).toHaveBeenCalledTimes(2);
  });
});
