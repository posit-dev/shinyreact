/**
 * `@posit/shinyreact` — the ESM entry for bundler-tier apps.
 *
 * Import the hooks directly instead of reading `window.shinyreact`; React and
 * ReactDOM are peer dependencies resolved by your bundler (so dev builds get
 * a development React with Fast Refresh). Built from the same source as the
 * IIFE bundle the server packages ship, so both speak the same protocol
 * version. See decisions/2026-08-17-js-distribution.md.
 */

// Side-effect import so the lib build emits the stylesheet as an asset. Vite
// does NOT auto-inject a CSS import into a lib-mode ESM bundle, so importing
// this here does not force CSS on consumers — it only produces the file they
// reach through the package's "./styles" export. Without it the build emitted
// no CSS at all, and ImageOutput's placeholder spinner had no @keyframes spin.
import "./shinyreact.css";

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
