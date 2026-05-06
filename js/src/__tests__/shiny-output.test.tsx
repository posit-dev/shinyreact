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

  it("renders a container with the given id and class", () => {
    const { container } = render(
      <ShinyOutput id="my_plot" className="plotly-output" />,
    );
    const inner = container.querySelector("#my_plot");
    expect(inner).not.toBeNull();
    expect(inner?.classList.contains("plotly-output")).toBe(true);
    expect(inner?.tagName).toBe("DIV");
  });

  it("renders a custom element when tagName is specified", () => {
    const { container } = render(
      <ShinyOutput id="my_table" tagName="shiny-data-frame" />,
    );
    const inner = container.querySelector("#my_table");
    expect(inner).not.toBeNull();
    expect(inner?.tagName.toLowerCase()).toBe("shiny-data-frame");
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

  it("passes additional props to the inner element", () => {
    const { container } = render(
      <ShinyOutput
        id="my_plot"
        className="plotly-output"
        style={{ height: "400px" }}
        data-testid="plot-container"
      />,
    );
    const inner = container.querySelector("#my_plot") as HTMLElement;
    expect(inner?.style.height).toBe("400px");
    expect(inner?.dataset.testid).toBe("plot-container");
  });

  it("is a no-op when window.Shiny is not available", () => {
    delete (window as any).Shiny;
    expect(() =>
      render(<ShinyOutput id="my_plot" className="plotly-output" />),
    ).not.toThrow();
  });

  it("bindAll scope is the wrapper, not the inner element", () => {
    const { container } = render(
      <ShinyOutput id="my_plot" className="plotly-output" />,
    );
    const wrapper = container.firstElementChild;
    const inner = container.querySelector("#my_plot");
    expect(mockBindAll).toHaveBeenCalledWith(wrapper);
    expect(wrapper).not.toBe(inner);
    expect(wrapper?.contains(inner!)).toBe(true);
  });
});
