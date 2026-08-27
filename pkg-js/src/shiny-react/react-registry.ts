import { getShiny } from "./get-shiny";
import { InputRegistry } from "./input-registry";
import { OutputRegistry } from "./output-registry";

export interface ShinyReactRegistry {
  inputs: InputRegistry;
  outputs: OutputRegistry;
}

let moduleRegistry: ShinyReactRegistry | undefined = undefined;

/** The module-local registry pair, created once on first use. */
function localRegistry(): ShinyReactRegistry {
  moduleRegistry ??= {
    inputs: new InputRegistry(),
    outputs: new OutputRegistry(),
  };
  return moduleRegistry;
}

/**
 * Attach the registry to `window.Shiny` eagerly, during shinyreact's one-time
 * init. Idempotent: repeated calls return the same registries rather than
 * building new ones, because rebuilding would silently discard every input
 * value and output subscriber the page had accumulated.
 */
export function initializeReactRegistry(): void {
  getReactRegistry();
}

/**
 * The registry pair for this *page*.
 *
 * Page-scoped for the reason spelled out in CLAUDE.md: two copies of this
 * library can be on one page (the server injects the IIFE even for npm-tier
 * apps until #217), and two registries would split one input id's producers
 * from its consumers. `??=` so the first copy to run owns the page and later
 * copies adopt it.
 *
 * Never returns `undefined`: with Shiny present it used to read
 * `shiny.reactRegistry` unchecked, which yielded `undefined` if init had not
 * run — a crash one call later, far from the cause.
 */
export function getReactRegistry(): ShinyReactRegistry {
  const shiny = getShiny();
  if (!shiny) {
    return localRegistry();
  }
  return (shiny.reactRegistry ??= localRegistry());
}

/** Test-only: drop the module-local registries so a fixture starts clean. */
export function _resetReactRegistryForTesting(): void {
  moduleRegistry = undefined;
}
