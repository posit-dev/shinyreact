/**
 * `@posit/shinyreact` — the ESM entry for bundler-tier apps.
 *
 * Import the hooks directly instead of reading `window.shinyreact`; React and
 * ReactDOM are peer dependencies resolved by your bundler (so dev builds get
 * a development React with Fast Refresh). Built from the same source as the
 * IIFE bundle the server packages ship, so both speak the same protocol
 * version. See decisions/2026-08-17-js-distribution.md.
 */

import { requireShinyReactConfigTag } from "./shiny-react/config";

// An independently-installed client meeting a page without the
// `#shinyreact-config` tag means the server predates the wire protocol —
// fail loudly instead of degrading silently (see protocol/README.md §4).
requireShinyReactConfigTag();

export {
  useSetShinyInput,
  useShinyBusy,
  useShinyInput,
  useShinyInputValue,
  useShinyOutputStatus,
  useShinyOutputValue,
  useShinyMessageHandler,
  useShinyInitialized,
  ImageOutput,
  MISSING,
  ShinyModuleProvider,
  ShinyReactComponentElement,
} from "./shiny-react";
export { ShinyOutput } from "./shiny-output";
export { PROTOCOL_VERSION } from "./shiny-react/config";
