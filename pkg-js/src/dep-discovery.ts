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
 * The `.shinyreact_init` ping routes a value through the server-side
 * `shinyreact.default` input handler — the hook that installs discovery — so
 * it works even in apps with no `useShinyInput`. Python's handler is a
 * pass-through, so the ping is a harmless no-op input there.
 */
export function installDepDiscovery(): void {
  if (typeof document === "undefined") return;

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
      shiny.setInputValue?.(".shinyreact_init:shinyreact.default", 1);
    });
  };

  if (getShiny()) {
    start();
  } else {
    document.addEventListener("shiny:connected", start, { once: true });
  }
}
