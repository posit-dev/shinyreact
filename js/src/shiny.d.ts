/**
 * Minimal type declarations for Shiny's global JavaScript API.
 * Used only by the output binding in index.ts.
 *
 * Note: shiny-react/index.ts separately declares `Window.Shiny?` as the
 * richer `ShinyClassExtended` type (from @posit/shiny). That declaration
 * covers the hooks' usage via `getShiny()`. The two type scopes are
 * intentionally separate — this ambient `const Shiny` assumes Shiny is
 * always present (true for the output binding), while the Window extension
 * marks it optional (safe for hooks that may run before Shiny loads).
 */
declare global {
  function $(selector: string | Element | JQuery): JQuery;

  interface JQuery {
    find(selector: string): JQuery;
    [index: number]: Element;
    length: number;
  }

  const Shiny: {
    OutputBinding: {
      new (): ShinyOutputBinding;
      prototype: ShinyOutputBinding;
    };
    outputBindings: {
      register(binding: ShinyOutputBinding, name: string): void;
    };
  };

  interface ShinyOutputBinding {
    find(scope: Element): ArrayLike<Element>;
    getId(el: Element): string;
    renderValue(el: Element, data: unknown): void;
    renderError(el: Element, err: { message: string; type?: string }): void;
    clearError(el: Element): void;
    showProgress(el: Element, show: boolean): void;
  }
}

export {};
