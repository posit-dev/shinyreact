/* eslint-disable @typescript-eslint/no-explicit-any */

import { getShiny } from "./get-shiny";

export type ErrorsMessageValue = {
  message: string;
  call: string[];
  type?: string[];
};

export type OutputStatus = "pending" | "ready" | "recalculating" | "error";

export class OutputRegistryEntry<T> {
  id: string;
  /**
   * The div this entry's binding renders into, inside the registry's hidden
   * container. Held as a reference rather than re-found by id at cleanup time:
   * output ids are author-chosen, so a document-wide lookup can match the
   * app's own markup instead of ours.
   */
  el?: HTMLElement;
  private status: OutputStatus = "pending";
  private hasValue = false;
  // Cached most-recent value and error so a late-mounting subscriber can be
  // synced to the entry's current state without waiting for the next server
  // update. Without these, `OutputRegistry.add` would push status (e.g.
  // "ready" / "error") into the new subscriber while leaving its value/error
  // useState slots at their initial defaults — divergent state.
  private lastValue: T | undefined = undefined;
  private lastError: ErrorsMessageValue | null = null;
  private useStateSetValueFns: Set<(value: T) => void>;
  private useStateSetStatusFns: Set<(status: OutputStatus) => void>;
  private useStateSetErrorFns: Set<(err: ErrorsMessageValue | null) => void>;

  constructor(id: string) {
    this.id = id;
    this.useStateSetValueFns = new Set();
    this.useStateSetStatusFns = new Set();
    this.useStateSetErrorFns = new Set();
  }

  hasReceivedValue(): boolean {
    return this.hasValue;
  }

  getLastValue(): T | undefined {
    return this.lastValue;
  }

  getLastError(): ErrorsMessageValue | null {
    return this.lastError;
  }

  addUseStateSetValueFn(fn: (value: T) => void) {
    this.useStateSetValueFns.add(fn);
  }

  removeUseStateSetValueFn(fn: (value: T) => void) {
    this.useStateSetValueFns.delete(fn);
  }

  addUseStateSetStatusFn(fn: (status: OutputStatus) => void) {
    this.useStateSetStatusFns.add(fn);
  }

  removeUseStateSetStatusFn(fn: (status: OutputStatus) => void) {
    this.useStateSetStatusFns.delete(fn);
  }

  addUseStateSetErrorFn(fn: (err: ErrorsMessageValue | null) => void) {
    this.useStateSetErrorFns.add(fn);
  }

  removeUseStateSetErrorFn(fn: (err: ErrorsMessageValue | null) => void) {
    this.useStateSetErrorFns.delete(fn);
  }

  getStatus(): OutputStatus {
    return this.status;
  }

  private setStatus(status: OutputStatus) {
    if (this.status === status) return;
    this.status = status;
    this.useStateSetStatusFns.forEach((fn) => fn(status));
  }

  setValue(value: T) {
    this.hasValue = true;
    this.lastValue = value;
    this.useStateSetValueFns.forEach((fn) => fn(value));
    // Receiving a value clears any prior error.
    if (this.status === "error") {
      this.lastError = null;
      this.useStateSetErrorFns.forEach((fn) => fn(null));
    }
    this.setStatus("ready");
  }

  setRecalculating(recalculating: boolean) {
    if (recalculating) {
      // Only flip to "recalculating" if we have already shown a value.
      // Before the first value arrives, the UI should keep showing the
      // pending/skeleton state — the server being busy doesn't change that.
      if (this.hasValue) {
        // Entering recalculating means the server is computing a fresh
        // result; any previous error is no longer relevant. Clear it so
        // status and error stay consistent (an existing error subscriber
        // shouldn't keep rendering the stale error while status says
        // "recalculating").
        if (this.status === "error") {
          this.lastError = null;
          this.useStateSetErrorFns.forEach((fn) => fn(null));
        }
        this.setStatus("recalculating");
      }
    } else {
      // Done recalculating: return to "ready" if we have a value, otherwise
      // stay in whatever state we were in (pending or error).
      if (this.hasValue && this.status === "recalculating") {
        this.setStatus("ready");
      }
    }
  }

  setError(err: ErrorsMessageValue) {
    this.lastError = err;
    this.useStateSetErrorFns.forEach((fn) => fn(err));
    this.setStatus("error");
  }

  isEmpty(): boolean {
    return (
      this.useStateSetValueFns.size === 0 &&
      this.useStateSetStatusFns.size === 0 &&
      this.useStateSetErrorFns.size === 0
    );
  }
}

export class OutputRegistry {
  private outputs: Map<string, OutputRegistryEntry<any>> = new Map();
  private bindAllScheduled = false;
  private container: HTMLElement;

  constructor() {
    const div = document.createElement("div");
    div.className = "shiny-react-output-container";
    div.style.visibility = "hidden";
    this.container = div;
    document.body.appendChild(this.container);
  }

  add<T>(
    outputId: string,
    setValue: (value: T) => void,
    setStatus: (status: OutputStatus) => void,
    setError: (err: ErrorsMessageValue | null) => void,
  ): () => void {
    let outputEntry = this.get(outputId);
    if (!outputEntry) {
      const div = document.createElement("div");
      div.className = "shiny-react-output";
      div.id = outputId;
      div.textContent = `This is the output div for ${outputId}`;
      this.container.appendChild(div);

      outputEntry = new OutputRegistryEntry(outputId);
      outputEntry.el = div;
      this.outputs.set(outputId, outputEntry);

      this.scheduleBindAll();
    }

    outputEntry.addUseStateSetValueFn(setValue);
    outputEntry.addUseStateSetStatusFn(setStatus);
    outputEntry.addUseStateSetErrorFn(setError);

    // Sync new subscriber with the entry's current state. Without all three
    // of these, a late-mounting subscriber would see status "ready" / "error"
    // while its local value/error useState slots still hold their initial
    // defaults — divergent state until the next server update.
    if (outputEntry.hasReceivedValue()) {
      setValue(outputEntry.getLastValue() as T);
    }
    setStatus(outputEntry.getStatus());
    if (outputEntry.getStatus() === "error") {
      setError(outputEntry.getLastError());
    }

    return () => {
      outputEntry.removeUseStateSetValueFn(setValue);
      outputEntry.removeUseStateSetStatusFn(setStatus);
      outputEntry.removeUseStateSetErrorFn(setError);
      this.scheduleCleanup(outputId);
    };
  }

  has(outputId: string) {
    return this.outputs.has(outputId);
  }

  get(outputId: string) {
    return this.outputs.get(outputId);
  }

  private scheduleCleanup(outputId: string) {
    requestAnimationFrame(() => {
      const entry = this.outputs.get(outputId);
      if (!entry || !entry.isEmpty()) {
        return;
      }

      this.outputs.delete(outputId);
      entry.el?.remove();
      this.scheduleBindAll();
    });
  }

  /**
   * Schedules a Shiny binding operation to run after DOM updates are complete.
   *
   * Note: I'm not sure if this is 100% reliable. I believe we need to avoid
   * overlapping calls to bindAll(), and am not sure if requestAnimationFrame()
   * will provide perfect reliability for this.
   */
  private scheduleBindAll() {
    const shiny = getShiny();
    if (!shiny) {
      return;
    }

    if (this.bindAllScheduled) {
      return;
    }

    this.bindAllScheduled = true;

    // Use requestAnimationFrame to ensure DOM updates are complete
    requestAnimationFrame(() => {
      shiny.unbindAll?.(this.container);
      // eslint-disable-next-line @typescript-eslint/no-floating-promises
      shiny.bindAll?.(this.container);
      this.bindAllScheduled = false;
    });
  }
}

/**
 * Create and register the React output binding when Shiny is available
 */
export function createReactOutputBinding() {
  const shiny = getShiny();
  if (!shiny) {
    return;
  }

  class ReactOutputBinding extends shiny.OutputBinding {
    override find(
      scope: HTMLElement | JQuery<HTMLElement>,
    ): JQuery<HTMLElement> {
      return $(scope).find(".shiny-react-output");
    }

    override renderValue(el: HTMLElement, data: any): void {
      const outputEntry = shiny!.reactRegistry?.outputs.get(el.id);
      if (!outputEntry) {
        console.error(`Output ${el.id} not found`);
        return;
      }
      outputEntry.setValue(data);
    }

    override renderError(el: HTMLElement, err: ErrorsMessageValue): void {
      console.error(`Error for ${el.id}:`, err);
      const outputEntry = shiny!.reactRegistry?.outputs.get(el.id);
      if (outputEntry) {
        outputEntry.setError(err);
      }
    }

    override showProgress(el: HTMLElement, show: boolean): void {
      const outputEntry = shiny!.reactRegistry?.outputs.get(el.id);
      if (!outputEntry) {
        console.error(`Output ${el.id} not found`);
        return;
      }
      outputEntry.setRecalculating(show);
    }
  }

  shiny.outputBindings.register(new ReactOutputBinding(), "shiny.reactOutput");
}
