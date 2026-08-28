/**
 * Mount a real example's `www/ui.js` in jsdom and drive it like a server.
 *
 * Lives with the examples, not with the package source: these are the example
 * apps' own tests. `pkg-js`'s vitest config includes them so a change to the
 * hooks that breaks an example fails the package's own test run.
 *
 * The point is to test the *client the example ships*, not a copy of it: the
 * file is read off disk and evaluated the way a browser evaluates a classic
 * script, against the real `window.shinyreact` global (`installGlobal()`) and
 * the real hooks + registries. Only Shiny itself is faked, so an assertion
 * here fails when the example changes — which is what makes the `(test)`
 * leaves in each example's `FEATURES.md` worth trusting.
 *
 * Limits, stated so nobody assumes otherwise:
 * - Examples whose `www/ui.js` is a build artifact (03, 04, 09) are
 *   gitignored and cannot be mounted here.
 * - The fake Shiny does not run bindings, so `ShinyOutput`-hosted widgets
 *   render as the empty element the binding would attach to, nothing more.
 * - jsdom has no layout, so anything reading element geometry is untestable.
 */
import { act } from "@testing-library/react";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { vi } from "vitest";

import { installGlobal } from "../../pkg-js/src/global";
import { _resetConfigTagRequirementForTesting } from "../../pkg-js/src/shiny-react/config";
import { __resetLifecycleStoreForTests } from "../../pkg-js/src/shiny-react/lifecycle-store";
import {
  _resetReactRegistryForTesting,
  getReactRegistry,
} from "../../pkg-js/src/shiny-react/react-registry";
import { _resetShinyReactInitializedForTesting } from "../../pkg-js/src/shiny-react/use-shiny";

const EXAMPLES_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);

/** One `Shiny.setInputValue()` call, in the order the client made it. */
export interface InputCall {
  /** The wire id, including any `:type` suffix the hook appended. */
  wireId: string;
  value: unknown;
  opts: unknown;
}

export interface MountedExample {
  /** The example's mount container (the div it appended to `<body>`). */
  readonly container: HTMLElement;
  /** Every `Shiny.setInputValue()` call the client has made so far. */
  readonly inputCalls: InputCall[];
  /** Pretend the server sent a value for `outputId`. */
  setOutput(outputId: string, value: unknown): Promise<void>;
  /** Pretend the server started recalculating `outputId`. */
  setRecalculating(outputId: string, recalculating: boolean): Promise<void>;
  /** The most recent value sent for `wireId`, or `undefined` if never sent. */
  lastInput(wireId: string): unknown;
  /** Run `fn` and flush React effects and state updates. */
  flush(fn?: () => void): Promise<void>;
  /**
   * Wait out `useShinyInput`'s debounce (100 ms by default) so debounced
   * `setInputValue` calls have landed in `inputCalls`.
   */
  settleDebounce(ms?: number): Promise<void>;
  /** Remove the mounted DOM and the fake Shiny. */
  cleanup(): void;
}

/**
 * Read and evaluate `examples/<name>/www/ui.js`.
 *
 * @param name the example directory, e.g. `"01-hello"`.
 */
export async function mountExample(name: string): Promise<MountedExample> {
  const file = path.join(EXAMPLES_DIR, name, "www", "ui.js");
  if (!fs.existsSync(file)) {
    throw new Error(
      `mountExample("${name}"): ${file} does not exist. Examples that build ` +
        `their client (03, 04, 09) gitignore www/ui.js and cannot be mounted.`,
    );
  }

  _resetReactRegistryForTesting();
  _resetShinyReactInitializedForTesting();
  _resetConfigTagRequirementForTesting();
  __resetLifecycleStoreForTests();
  document.body.innerHTML = "";

  const inputCalls: InputCall[] = [];
  (window as any).Shiny = {
    // Resolved, so `useShinyInitialized()` flips true on the first flush.
    initializedPromise: Promise.resolve(),
    setInputValue: (wireId: string, value: unknown, opts: unknown) => {
      inputCalls.push({ wireId, value, opts });
    },
    OutputBinding: class {},
    outputBindings: { register: () => {} },
    addCustomMessageHandler: () => {},
    bindAll: vi.fn(),
    unbindAll: vi.fn(),
  };

  installGlobal();

  const source = fs.readFileSync(file, "utf-8");
  await act(async () => {
    // A classic script, evaluated the way the browser would: no imports, no
    // exports, `window.shinyreact` already installed.
    new Function(source)();
    await Promise.resolve();
  });

  // The output registry also appends a hidden host to <body>; the example's
  // own mount container is the other one.
  const container = [...document.body.children].find(
    (el) => !el.classList.contains("shiny-react-output-container"),
  ) as HTMLElement | undefined;
  if (!container) {
    throw new Error(`mountExample("${name}"): the client mounted nothing.`);
  }

  const flush = async (fn?: () => void): Promise<void> => {
    await act(async () => {
      fn?.();
      await Promise.resolve();
    });
  };

  const entry = (outputId: string) => {
    const found = getReactRegistry().outputs.get(outputId);
    if (!found) {
      throw new Error(
        `No component subscribed to output "${outputId}" — a client that ` +
          `never calls useShinyOutputValue("${outputId}") cannot be fed one.`,
      );
    }
    return found;
  };

  return {
    container,
    inputCalls,
    setOutput: (outputId, value) => flush(() => entry(outputId).setValue(value)),
    setRecalculating: (outputId, recalculating) =>
      flush(() => entry(outputId).setRecalculating(recalculating)),
    settleDebounce: async (ms = 150) => {
      await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, ms));
      });
    },
    lastInput: (wireId) => {
      const matching = inputCalls.filter((c) => c.wireId === wireId);
      return matching[matching.length - 1]?.value;
    },
    flush,
    cleanup: () => {
      document.body.innerHTML = "";
      delete (window as any).Shiny;
    },
  };
}
