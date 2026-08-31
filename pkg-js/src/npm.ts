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

import { installDepDiscovery } from "./dep-discovery";

// Two copies on one page: this app bundles `@posit/shinyreact` AND the server
// served shinyreact.js, because the page entry point left `shinyreact_js` at its
// default of "server". It still works — the registries are page-scoped, so the
// two copies share one set of inputs, outputs, and message handlers — but the
// page downloads and parses a whole second React + hooks for nothing.
//
// A warning rather than a throw: nothing is broken, and taking down a working
// app over wasted bytes would be the wrong trade. It lives here, in the entry,
// because only the npm build can detect this — deferred classic scripts and
// module scripts execute in document order, and the page emits the bundle
// dependency before the app's, so by the time this runs the global is already
// installed if it is going to be. `installGlobal()` runs first and sees nothing.
if (
  typeof window !== "undefined" &&
  (window as { shinyreact?: unknown }).shinyreact
) {
  console.warn(
    "[shinyreact] shinyreact.js is loaded twice on this page: the server " +
      "served it, and this app also imports @posit/shinyreact. The app works, " +
      "but it is downloading a second copy of React and the hooks for " +
      'nothing. Pass shinyreact_js="client" to your page entry point — ' +
      "page_react(), page_react_html(), set_react_page(), or ReactApp().",
  );
}

// Automatic renderer dependency discovery, same as the IIFE bundle installs.
// Without this an npm-tier app gets no `shinyreact-deps` handler AND never
// sends the `.shinyreact_init` ping, so an R server never even installs
// discovery for the session — a `<ShinyOutput>` whose binding arrives late
// silently never binds.
//
// Safe as an import-time side effect: it no-ops without `document` (SSR, node
// tests), and with no Shiny yet it only adds one event listener. See
// dep-discovery.ts.
installDepDiscovery();

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
