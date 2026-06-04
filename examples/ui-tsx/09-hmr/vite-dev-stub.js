import fs from "node:fs";
import path from "node:path";

// The contents of the dev-mode `www/app.js`. Shiny serves this file statically.
// It (1) installs the React Fast Refresh preamble that @vitejs/plugin-react
// normally injects into the HTML it serves — but here Shiny serves the page, so
// we install it ourselves — then (2) dynamically imports Vite's HMR client and
// the real entry from the dev server. Dynamic `import()` is required: static
// imports are hoisted and would run the entry BEFORE the preamble, which makes
// Fast Refresh fall back to a full page reload.
export function makeDevStub(origin, entry) {
  origin = origin.replace(/\/+$/, "");
  return (
    `import RefreshRuntime from ${JSON.stringify(`${origin}/@react-refresh`)};\n` +
    `RefreshRuntime.injectIntoGlobalHook(window);\n` +
    `window.$RefreshReg$ = () => {};\n` +
    `window.$RefreshSig$ = () => (type) => type;\n` +
    `window.__vite_plugin_react_preamble_installed__ = true;\n` +
    `await import(${JSON.stringify(`${origin}/@vite/client`)});\n` +
    `await import(${JSON.stringify(`${origin}/${entry}`)});\n`
  );
}

// Vite plugin (serve only). On dev-server start it writes `outFile` (e.g.
// www/app.js) as the dev stub, and removes it on shutdown so a later plain
// `shiny run` doesn't load a stub pointing at a dead dev server. `vite build`
// (apply:"serve" excludes this plugin) overwrites `outFile` with the real bundle.
export function shinyreactDevStub({ entry, outFile }) {
  let stubPath;
  return {
    name: "shinyreact-dev-stub",
    apply: "serve",
    configResolved(config) {
      stubPath = path.resolve(config.root, outFile);
    },
    configureServer(server) {
      const port = server.config.server.port ?? 5173;
      const origin = `http://localhost:${port}`;
      fs.writeFileSync(stubPath, makeDevStub(origin, entry));
      server.config.logger.info(`  shinyreact: wrote dev stub ${outFile} -> ${origin}`);

      const remove = () => {
        try {
          fs.unlinkSync(stubPath);
        } catch {
          /* already gone */
        }
      };
      server.httpServer?.once("close", remove);
      for (const sig of ["SIGINT", "SIGTERM"]) {
        process.once(sig, () => {
          remove();
          process.exit(0);
        });
      }
    },
  };
}
