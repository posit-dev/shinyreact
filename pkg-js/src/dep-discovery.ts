import { getShiny } from "./shiny-react/get-shiny";

/**
 * Client half of automatic renderer dependency discovery (issues #146/#203;
 * server half in `pkg-r/R/dep-discovery.R`).
 *
 * After each reactive flush the server diffs its registered outputs and
 * pushes any new outputs' HTML dependencies (binding JS/CSS such as
 * `htmlwidgets.js`, `plotly-binding`) as a `shinyreact-deps` custom message.
 * We load them, then re-run `bindAll` so `<ShinyOutput>` elements that
 * mounted before their binding existed get bound. `bindAll` skips elements
 * already marked `.shiny-bound-*`, so re-running it page-wide is safe, and
 * the shiny client replays stored output values on late bind.
 *
 * The `.shinyreact_init` ping routes through the server-side
 * `shinyreact.init` input handler, whose job is per-session bootstrap
 * (installing discovery in R), so it works even in apps with no
 * `useShinyInput`. Python registers the same handler as a no-op today —
 * its bootstrap hook for posit-dev/shinyreact#220.
 */
let installed = false;

/** Test-only: allow re-installing in a fresh fixture. */
export function _resetDepDiscoveryForTesting(): void {
  installed = false;
}

export function installDepDiscovery(): void {
  // Import-time safe by construction, which is what lets BOTH entry points
  // call it: no `document` (SSR, node tests) is a no-op, no Shiny yet means a
  // single event listener and nothing else, and calling it twice is a no-op.
  if (typeof document === "undefined") return;
  if (installed) return;
  installed = true;

  const start = (): void => {
    const shiny = getShiny();
    if (!shiny) return;
    shiny.addCustomMessageHandler("shinyreact-deps", async (deps: unknown) => {
      try {
        const s = shiny as unknown as {
          renderDependenciesAsync?: (deps: unknown) => Promise<unknown>;
          bindAll?: (scope: Element) => unknown;
        };
        await s.renderDependenciesAsync?.(deps);
        await s.bindAll?.(document.documentElement);
      } catch (err) {
        console.error("[shinyreact] failed to load pushed dependencies:", err);
      }
    });
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    shiny.initializedPromise.then(() => {
      shiny.setInputValue?.(".shinyreact_init:shinyreact.init", 1);
    });
  };

  if (getShiny()) {
    start();
    return;
  }

  // Wait for Shiny. NOT `{ once: true }`: `shiny:connected` can fire before
  // `window.Shiny` is readable, and a one-shot listener would consume the
  // event, leave `start()` a no-op, and never install discovery at all. Stay
  // subscribed until Shiny is actually there, then unsubscribe.
  const onConnected = (): void => {
    if (!getShiny()) return;
    document.removeEventListener("shiny:connected", onConnected);
    start();
  };
  document.addEventListener("shiny:connected", onConnected);
}
