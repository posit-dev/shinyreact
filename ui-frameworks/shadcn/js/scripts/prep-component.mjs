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
// @shiny type=TODO children=false props=PROP:TYPE
//   type    : Display | Container | Input | Action | Overlay | Collection | Hybrid | Push
//   children: true (takes *children / ...) | false (leaf)
//   props   : comma-separated  name:type[=default]
//     types : str  int  float  bool  list
//     no =  : required positional; =None : optional null; =val : optional with default
//     class_:str=None is always the last prop — maps to className on the wire
//   e.g.  @shiny type=Input children=false props=input_id:str,label:str=None,class_:str=None
//   e.g.  @shiny type=Overlay children=true props=input_id:str,trigger_label:str=Open,class_:str=None
//   When done: node scripts/finalize-component.mjs ${name}
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
console.log(`✓ wrote src/components/${name}.jsx

Two-phase workflow:

Phase 1 — fill the bridge (you / Claude):
  a. Open src/components/${name}.jsx
  b. Replace type=TODO with the real type, fill props=, set children=true/false
  c. Write the bridge logic (hook, props destructure, JSX)

Phase 2 — mechanical integration (script):
  node scripts/finalize-component.mjs ${name}
  → reads @shiny annotation, writes index.jsx + Python + R helpers automatically

Then build + verify:
  npm run build

See scaffold-component skill for bridge patterns and the @shiny annotation format.
`);
