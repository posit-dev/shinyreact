/**
 * Type declarations for Shiny's global JavaScript API.
 * Shiny is loaded by the browser before shinyjson.js runs.
 */
declare global {
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
