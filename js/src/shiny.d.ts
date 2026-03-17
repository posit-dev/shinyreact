/**
 * Type declarations for Shiny's global JavaScript API.
 * Shiny is loaded by the browser before shinyjson.js runs.
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
