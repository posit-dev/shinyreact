#!/usr/bin/env node
// Mechanical prep for wrapping a shadcn component as a shinyreact component.
//
// Does the deterministic, token-heavy parts so Claude/you only fill the fuzzy
// bridge logic:
//   1. strip TypeScript (keep JSX) from components-src/<name>.tsx
//   2. drop "use client" + neutralize the shadcn `export`s (bridge owns the export)
//   3. fix import paths (@/registry/.../ui/X -> @/components/X; button -> @/lib/button-base)
//   4. append a bridge stub (className wired, export { ShinyX as X })
//   5. write js/src/components/<name>.jsx (refuses to overwrite)
//   6. print the index.jsx lines + Python/R helper stubs + a checklist
//
// Usage (from js/):  node scripts/prep-component.mjs <name>
//   e.g.             node scripts/prep-component.mjs toggle

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";

const jsRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const srcDir = join(jsRoot, "src/components-src");
const outDir = join(jsRoot, "src/components");

const name = process.argv[2];
if (!name) {
  console.error("usage: node scripts/prep-component.mjs <name>");
  process.exit(1);
}

const tsxPath = join(srcDir, `${name}.tsx`);
if (!existsSync(tsxPath)) {
  console.error(`source not found: ${tsxPath}\n(run download-components.sh first)`);
  process.exit(1);
}

const outPath = join(outDir, `${name}.jsx`);
if (existsSync(outPath)) {
  console.error(`refusing to overwrite existing ${outPath}`);
  process.exit(1);
}

const pascal = name
  .split(/[-_]/)
  .map((s) => s[0].toUpperCase() + s.slice(1))
  .join("");

let code = readFileSync(tsxPath, "utf8");

// 2a. drop the "use client" directive
code = code.replace(/^\s*["']use client["'];?\s*\n/m, "");

// 1. strip TS types, keep JSX untouched
const { code: stripped } = await esbuild.transform(code, {
  loader: "tsx",
  jsx: "preserve",
});

let jsx = stripped;

// 3. fix import paths to our layout
jsx = jsx.replace(/@\/registry\/[^/]+\/ui\/button/g, "@/lib/button-base");
jsx = jsx.replace(/@\/registry\/[^/]+\/ui\//g, "@/components/");

// 2b. neutralize shadcn exports — the bridge owns the public export
jsx = jsx.replace(/export\s*\{[^}]*\};?/g, ""); // export { A, B }
jsx = jsx.replace(/\bexport\s+(function|const|class)\b/g, "$1"); // export function/const

const bridge = `
// --- shinyreact bridge ---
// TODO(you): choose the component type and wire it. Types:
//   Display      -> no hook; read props.
//   Input        -> useShinyInput(input_id, default)
//   Action       -> useShinyInput(id, 0, { debounceMs: 0, priority: "event" })
//   Overlay      -> useShinyInput(id, false) for open state + children
//   Collection   -> items prop array (see dropdown-menu.jsx)
//   Hybrid/Push  -> see tabs.jsx / sonner.jsx
// Forward className to the root via the component (it merges with cn()).
function Shiny${pascal}({ element, children }) {
  const { className } = element.props;
  return (
    <${pascal} className={className}>
      {children}
    </${pascal}>
  );
}

export { Shiny${pascal} as ${pascal} };
`;

writeFileSync(outPath, jsx.replace(/\n{3,}/g, "\n\n").trimEnd() + "\n" + bridge);

const snake = name.replace(/-/g, "_");
console.log(`✓ wrote src/components/${name}.jsx (shadcn source stripped + bridge stub)

Next (fill the fuzzy parts):

1. index.jsx — add:
     import { ${pascal} } from "@/components/${name}";
     "shadcn:${pascal}": ${pascal},

2. pkg-py/shadcn/__init__.py — add (class_ last, keyword-only):
     def ${snake}(input_id: str, *, class_: str | None = None) -> shinyreact.Node:
         return shinyreact.Node(
             type="shadcn:${pascal}",
             props={"input_id": input_id, "className": class_},
         )

3. pkg-r/shadcn.R — add (\`...\` separator + check_dots_empty, class last):
     shadcn_${snake} <- function(input_id, ..., class = NULL) {
       rlang::check_dots_empty()
       node("shadcn:${pascal}", props = list(input_id = input_id, className = class))
     }

4. Fill the bridge in src/components/${name}.jsx, then \`npm run build\` and screenshot.
`);
