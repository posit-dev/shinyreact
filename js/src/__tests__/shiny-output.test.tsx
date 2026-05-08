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

  it("does not re-bind when only unrelated props change", () => {
    const { rerender } = render(
      <ShinyOutput id="my_plot" className="a" />,
    );
    expect(mockBindAll).toHaveBeenCalledTimes(1);

    rerender(<ShinyOutput id="my_plot" className="b" />);
    rerender(<ShinyOutput id="my_plot" className="b" style={{ color: "red" }} />);
    rerender(<ShinyOutput id="my_plot" className="b" style={{ color: "red" }} />);

    expect(mockBindAll).toHaveBeenCalledTimes(1);
    expect(mockUnbindAll).toHaveBeenCalledTimes(0);
  });

  it("calls unbindAll before bindAll when id changes", () => {
    const calls: string[] = [];
    mockBindAll.mockImplementation(() => calls.push("bind"));
    mockUnbindAll.mockImplementation(() => calls.push("unbind"));

    const { rerender } = render(<ShinyOutput id="first" />);
    rerender(<ShinyOutput id="second" />);

    // Mount, then on rerender: cleanup (unbind) then effect (bind).
    expect(calls).toEqual(["bind", "unbind", "bind"]);
  });

  it("unbinds the element that was previously bound when id changes", () => {
    // The cleanup closure captures the ref to the *previous* element. When
    // React updates props on the same DOM node, the captured element still
    // refers to the now-renamed node. unbindAll must be called with that
    // element (not a stale node from elsewhere).
    const { container, rerender } = render(<ShinyOutput id="first" />);
    const elBeforeRerender = container.querySelector("#first");

    rerender(<ShinyOutput id="second" />);
    const elAfterRerender = container.querySelector("#second");

    // React reuses the DOM node, so both queries return the same element.
    expect(elBeforeRerender).toBe(elAfterRerender);
    expect(mockUnbindAll).toHaveBeenCalledWith(elAfterRerender, true);
  });

  it("forwards event handlers (e.g., onClick) to the rendered element", () => {
    const onClick = vi.fn();
    const { container } = render(
      <ShinyOutput id="my_plot" onClick={onClick} />,
    );
    const el = container.querySelector("#my_plot") as HTMLElement;
    el.click();
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("forwards children to the rendered element (e.g., as fallback content)", () => {
    const { container } = render(
      <ShinyOutput id="my_plot">
        <span data-testid="fallback">loading…</span>
      </ShinyOutput>,
    );
    const el = container.querySelector("#my_plot");
    expect(el?.querySelector("[data-testid='fallback']")?.textContent).toBe(
      "loading…",
    );
  });

  it("does not throw when Shiny is present but bindAll is missing", () => {
    (window as any).Shiny = { unbindAll: mockUnbindAll };
    const { unmount } = render(<ShinyOutput id="my_plot" />);
    // bindAll missing → effect early-returns, so unbindAll is also a no-op.
    expect(mockUnbindAll).not.toHaveBeenCalled();
    expect(() => unmount()).not.toThrow();
  });

  it("does not throw when Shiny is present but unbindAll is missing", () => {
    (window as any).Shiny = { bindAll: mockBindAll };
    const { unmount } = render(<ShinyOutput id="my_plot" />);
    expect(mockBindAll).toHaveBeenCalledTimes(1);
    expect(() => unmount()).not.toThrow();
  });

  it("binds each ShinyOutput independently when multiple are rendered", () => {
    render(
      <div>
        <ShinyOutput id="a" />
        <ShinyOutput id="b" />
        <ShinyOutput id="c" />
      </div>,
    );
    expect(mockBindAll).toHaveBeenCalledTimes(3);
  });

  it("unmounting one ShinyOutput unbinds only that element, not its siblings", () => {
    // The functional payoff of `unbindAll(el, true)`: removing one output
    // from a shared parent must not touch sibling outputs' bindings.
    function App({ showA }: { showA: boolean }) {
      return (
        <div>
          {showA && <ShinyOutput id="a" />}
          <ShinyOutput id="b" />
          <ShinyOutput id="c" />
        </div>
      );
    }

    const { container, rerender } = render(<App showA={true} />);
    const elA = container.querySelector("#a");
    expect(mockBindAll).toHaveBeenCalledTimes(3);

    mockUnbindAll.mockClear();
    rerender(<App showA={false} />);

    expect(mockUnbindAll).toHaveBeenCalledTimes(1);
    expect(mockUnbindAll).toHaveBeenCalledWith(elA, true);
  });

  describe("error handling", () => {
    let errorSpy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
      errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    });

    afterEach(() => {
      errorSpy.mockRestore();
    });

    it("logs and stays mounted when bindAll throws synchronously", () => {
      const boom = new Error("boom");
      mockBindAll.mockImplementationOnce(() => {
        throw boom;
      });

      const { container } = render(<ShinyOutput id="my_plot" />);

      expect(errorSpy).toHaveBeenCalledTimes(1);
      expect(errorSpy.mock.calls[0][0]).toBe(
        '[shinyreact] ShinyOutput "my_plot" bindAll failed:',
      );
      expect(errorSpy.mock.calls[0][1]).toEqual({
        id: "my_plot",
        phase: "bindAll",
        error: boom,
      });
      expect(container.querySelector("#my_plot")).not.toBeNull();
    });

    it("logs and stays mounted when bindAll returns a rejecting promise", async () => {
      const boom = new Error("async boom");
      mockBindAll.mockReturnValueOnce(Promise.reject(boom));

      const { container } = render(<ShinyOutput id="my_plot" />);

      // Allow the rejection's .catch handler to run.
      await Promise.resolve();
      await Promise.resolve();

      expect(errorSpy).toHaveBeenCalledTimes(1);
      expect(errorSpy.mock.calls[0][0]).toBe(
        '[shinyreact] ShinyOutput "my_plot" bindAll failed:',
      );
      expect(errorSpy.mock.calls[0][1]).toEqual({
        id: "my_plot",
        phase: "bindAll",
        error: boom,
      });
      expect(container.querySelector("#my_plot")).not.toBeNull();
    });

    it("logs and does not re-throw when unbindAll throws on unmount", () => {
      const boom = new Error("teardown boom");
      mockUnbindAll.mockImplementationOnce(() => {
        throw boom;
      });

      const { unmount } = render(<ShinyOutput id="my_plot" />);

      expect(() => unmount()).not.toThrow();
      expect(errorSpy).toHaveBeenCalledTimes(1);
      expect(errorSpy.mock.calls[0][0]).toBe(
        '[shinyreact] ShinyOutput "my_plot" unbindAll failed:',
      );
      expect(errorSpy.mock.calls[0][1]).toEqual({
        id: "my_plot",
        phase: "unbindAll",
        error: boom,
      });
    });

    it("isolates a failing bindAll to one sibling — others still render and bind", () => {
      mockBindAll.mockImplementationOnce(() => {}); // a
      mockBindAll.mockImplementationOnce(() => {
        throw new Error("only b fails");
      });
      mockBindAll.mockImplementationOnce(() => {}); // c

      const { container } = render(
        <div>
          <ShinyOutput id="a" />
          <ShinyOutput id="b" />
          <ShinyOutput id="c" />
        </div>,
      );

      expect(container.querySelector("#a")).not.toBeNull();
      expect(container.querySelector("#b")).not.toBeNull();
      expect(container.querySelector("#c")).not.toBeNull();
      expect(mockBindAll).toHaveBeenCalledTimes(3);
      expect(errorSpy).toHaveBeenCalledTimes(1);
      expect(errorSpy.mock.calls[0][1]).toMatchObject({
        id: "b",
        phase: "bindAll",
      });
    });

    it("logs the new id when re-binding after id change throws", () => {
      const { rerender, container } = render(<ShinyOutput id="first" />);
      expect(errorSpy).not.toHaveBeenCalled();

      const boom = new Error("rebind boom");
      mockBindAll.mockImplementationOnce(() => {
        throw boom;
      });

      rerender(<ShinyOutput id="second" />);

      expect(errorSpy).toHaveBeenCalledTimes(1);
      expect(errorSpy.mock.calls[0][0]).toBe(
        '[shinyreact] ShinyOutput "second" bindAll failed:',
      );
      expect(errorSpy.mock.calls[0][1]).toEqual({
        id: "second",
        phase: "bindAll",
        error: boom,
      });
      expect(container.querySelector("#second")).not.toBeNull();
    });
  });

  it("ignores Shiny added to the window after mount", () => {
    // The effect captures Shiny synchronously on mount. If Shiny loads
    // later, this component does not retroactively bind — that's the
    // documented behavior (the surrounding page-level bindAll handles it).
    delete (window as any).Shiny;
    const { unmount } = render(<ShinyOutput id="my_plot" />);
    (window as any).Shiny = { bindAll: mockBindAll, unbindAll: mockUnbindAll };
    unmount();
    expect(mockBindAll).not.toHaveBeenCalled();
    expect(mockUnbindAll).not.toHaveBeenCalled();
  });
});
