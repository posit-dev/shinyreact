#!/usr/bin/env node
// Mechanical integration after the shinyreact bridge has been filled.
//
// Reads the @shiny annotation from the filled bridge and:
//   1. Idempotently inserts import + registry entry into src/index.jsx
//   2. Appends the Python helper to pkg-py/src/shinyshadcn/_<category>.py and
//      regenerates __init__.py's re-exports (skips the append if it exists)
//   3. Appends the R helper to pkg-r/R/<category>.R (skips if it exists); then
//      you re-run roxygen2 to refresh NAMESPACE + man/
//
// ANNOTATION FORMAT — one line in the bridge comment block:
//   // @shiny type=Input children=false props=input_id:str,total_pages:int=10,current:int=1
//
//   type     : Display | Container | Input | Action | Overlay | Collection | Hybrid | Push
//   category : (optional) inputs | display | overlays | menus | layout | feedback
//              which package module the helper lands in. Defaults from `type`;
//              set it when the default is wrong (e.g. a Hybrid that belongs in
//              inputs rather than layout).
//   children : true  (takes *children / ... in Python/R)
//              false (leaf — no children, R gets check_dots_empty)
//   props    : comma-separated  name:type[=default]
//     types     : str  int  float  bool  list
//     no =      → required positional arg
//     =None     → optional, null default
//     =<value>  → optional with default  (str values need no quotes; type implies context)
//   class_ : always the last prop; auto-added if omitted. Maps to className on the wire.
//            In R it becomes `class`.
//
// Usage (from js/):   node scripts/finalize-component.mjs <name>
//   e.g.              node scripts/finalize-component.mjs toggle

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const jsRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const pkgRoot = resolve(jsRoot, ".."); // ui-frameworks/shadcn/

// ── CLI arg ───────────────────────────────────────────────────────────────────

const name = process.argv[2];
if (!name) {
  console.error("usage: node scripts/finalize-component.mjs <name>");
  process.exit(1);
}

// ── Read component file ───────────────────────────────────────────────────────

const jsxPath = join(jsRoot, `src/components/${name}.jsx`);
if (!existsSync(jsxPath)) {
  console.error(
    `Component not found: ${jsxPath}\n` +
    `Run prep-component.mjs first, then fill the bridge.`,
  );
  process.exit(1);
}
const jsxSource = readFileSync(jsxPath, "utf8");

// ── Parse @shiny annotation ───────────────────────────────────────────────────

const annotationMatch = jsxSource.match(/\/\/\s*@shiny\s+(.+)/);
if (!annotationMatch) {
  console.error(
    `No @shiny annotation found in ${jsxPath}\n\n` +
    `Add this line to the bridge comment (replacing TODO values):\n` +
    `  // @shiny type=Input children=false props=input_id:str,label:str=None,class_:str=None\n\n` +
    `Types: Display Container Input Action Overlay Collection Hybrid Push\n` +
    `Prop types: str  int  float  bool  list`,
  );
  process.exit(1);
}

const ann = {};
for (const token of annotationMatch[1].trim().split(/\s+/)) {
  const eq = token.indexOf("=");
  if (eq !== -1) ann[token.slice(0, eq)] = token.slice(eq + 1);
}

if (!ann.type || ann.type === "TODO") {
  console.error(`@shiny annotation still has type=TODO. Set the real type first.`);
  process.exit(1);
}
if (!ann.props || ann.props === "PROP:TYPE") {
  console.error(
    `@shiny annotation has no props (or placeholder).\n` +
    `Example: props=input_id:str,total_pages:int=10,class_:str=None`,
  );
  process.exit(1);
}

const hasChildren = ann.children === "true";

// Parse each prop spec: "name:type[=default]"
function parsePropSpec(spec) {
  const eqIdx = spec.indexOf("=");
  if (eqIdx === -1) {
    const [n, t = "str"] = spec.split(":");
    return { name: n, type: t, rawDefault: undefined, required: true };
  }
  const rawDefault = spec.slice(eqIdx + 1);
  const [n, t = "str"] = spec.slice(0, eqIdx).split(":");
  return { name: n, type: t, rawDefault, required: false };
}

let props = ann.props.split(",").map(parsePropSpec);

// Ensure class_ is present and last
const classIdx = props.findIndex((p) => p.name === "class_");
if (classIdx === -1) {
  console.warn(`  [warn] class_ not in annotation — auto-adding as last prop.`);
  props.push({ name: "class_", type: "str", rawDefault: "None", required: false });
} else if (classIdx !== props.length - 1) {
  const [cp] = props.splice(classIdx, 1);
  props.push(cp);
}

// ── Extract export name ───────────────────────────────────────────────────────

const exportMatch = jsxSource.match(/export\s*\{\s*Shiny\w+\s+as\s+(\w+)\s*\}/);
if (!exportMatch) {
  console.error(
    `Could not find 'export { ShinyX as X }' in ${jsxPath}\n` +
    `The bridge must use this export form.`,
  );
  process.exit(1);
}
const exportName = exportMatch[1]; // e.g. "Pagination", "Toaster", "InputOtp"

// Derive snake names from the export (not the file name) so sonner → toaster, etc.
function toSnake(pascal) {
  return pascal
    .replace(/([A-Z])/g, (m, c, i) => (i === 0 ? c.toLowerCase() : "_" + c.toLowerCase()))
    .replace(/^_/, "");
}
const snake = toSnake(exportName); // Python fn name + R fn suffix

// ── Target package module (category) ───────────────────────────────────────────

const CATEGORIES = ["inputs", "display", "overlays", "menus", "layout", "feedback"];
const TYPE_TO_CATEGORY = {
  Display: "display",
  Container: "layout",
  Input: "inputs",
  Action: "inputs",
  Overlay: "overlays",
  Collection: "menus",
  Hybrid: "layout",
  Push: "feedback",
};
const category = ann.category ?? TYPE_TO_CATEGORY[ann.type] ?? "display";
if (!CATEGORIES.includes(category)) {
  console.error(`Unknown category "${category}". One of: ${CATEGORIES.join(", ")}`);
  process.exit(1);
}

// ── Type helpers ──────────────────────────────────────────────────────────────

const PY_BASE = { str: "str", int: "int", float: "float", bool: "bool", list: "list" };

function pyBase(t) { return PY_BASE[t] ?? "object"; }

function pyAnnotation(prop) {
  const { name, type, rawDefault, required } = prop;
  if (name === "class_") return "str | None = None";
  if (required)          return pyBase(type);
  if (rawDefault === "None") return `${pyBase(type)} | None = None`;
  if (type === "bool")   return `bool = ${rawDefault === "True" || rawDefault === "true" ? "True" : "False"}`;
  if (type === "int")    return `int = ${rawDefault}`;
  if (type === "float")  return `float = ${rawDefault}`;
  if (type === "list")   return "list | None = None";
  // str
  return `str = "${rawDefault}"`;
}

function rDefault(prop) {
  const { name, type, rawDefault } = prop;
  if (name === "class_")                      return "NULL";
  if (rawDefault === undefined)               return undefined; // required — no default shown
  if (rawDefault === "None")                  return "NULL";
  if (type === "bool")
    return rawDefault === "True" || rawDefault === "true" ? "TRUE" : "FALSE";
  if (type === "int")                         return `${rawDefault}L`;
  if (type === "float")                       return rawDefault;
  if (type === "list")                        return "NULL";
  // str
  return `"${rawDefault}"`;
}

// Wire key: class_ → className; everything else stays
function wireKey(name) { return name === "class_" ? "className" : name; }

// R param name: class_ → class
function rParam(name) { return name === "class_" ? "class" : name; }

// ── Generate Python helper ─────────────────────────────────────────────────────

function generatePython() {
  const required = props.filter((p) => p.required);
  const optional = props.filter((p) => !p.required); // includes class_

  // Signature lines (always multi-line to stay under ruff's 88-char limit)
  const sigLines = [];
  for (const p of required) sigLines.push(`    ${p.name}: ${pyBase(p.type)},`);
  sigLines.push(hasChildren ? "    *children: object," : "    *,");
  for (const p of optional)  sigLines.push(`    ${p.name}: ${pyAnnotation(p)},`);

  // Docstring arg lines
  const docLines = [];
  for (const p of required)
    docLines.push(`        ${p.name}: TODO.`);
  if (hasChildren)
    docLines.push(`        *children: Content nodes rendered inside the component.`);
  for (const p of optional) {
    if (p.name === "class_")
      docLines.push(`        class_: Extra CSS classes merged onto the root element.`);
    else
      docLines.push(`        ${p.name}: TODO.`);
  }

  // Props dict (exclude class_; add className at end)
  const nonClass = props.filter((p) => p.name !== "class_");
  const propsLines = nonClass.map((p) => `            "${wireKey(p.name)}": ${p.name},`);
  propsLines.push(`            "className": class_,`);

  // Node construction
  const nodeLines = [
    `        type="shadcn:${exportName}",`,
    `        props={`,
    ...propsLines,
    `        },`,
  ];
  if (hasChildren) nodeLines.push(`        children=list(children),`);

  return [
    ``,
    `def ${snake}(`,
    ...sigLines,
    `) -> shinyreact.Node:`,
    `    """TODO: one-line description.`,
    ``,
    `    Args:`,
    ...docLines,
    `    """`,
    `    return shinyreact.Node(`,
    ...nodeLines,
    `    )`,
  ].join("\n");
}

// ── Generate R helper ──────────────────────────────────────────────────────────

function generateR() {
  const required = props.filter((p) => p.required);
  const optional = props.filter((p) => !p.required);
  const fnName   = `shadcn_${snake}`;

  // Signature params
  const params = [...required.map((p) => p.name), "..."];
  for (const p of optional) {
    const d = rDefault(p);
    params.push(`${rParam(p.name)} = ${d}`);
  }

  // Single-line signature attempt; air format will re-wrap if needed
  const sig = `${fnName} <- function(${params.join(", ")}) {`;

  // Roxygen docs
  const docLines = [`#' TODO: one-line description.`];
  for (const p of required)
    docLines.push(`#' @param ${p.name} TODO.`);
  docLines.push(
    hasChildren
      ? `#' @param ... Content nodes rendered inside the component.`
      : `#' @param ... Must be empty (leaf component).`,
  );
  for (const p of optional) {
    if (p.name === "class_") {
      docLines.push(`#' @param class Extra CSS classes merged onto the root element.`);
    } else {
      const d = rDefault(p);
      docLines.push(`#' @param ${rParam(p.name)} TODO (default ${d}).`);
    }
  }
  docLines.push(`#' @return A \`shinyreact\` node.`);
  docLines.push(`#' @export`);

  // Props list with aligned =
  const allProps = props; // includes class_
  const maxKey = Math.max(...allProps.map((p) => wireKey(p.name).length));
  const propLines = allProps.map((p) => {
    const wk  = wireKey(p.name);
    const pad = " ".repeat(maxKey - wk.length);
    const val = rParam(p.name); // R variable name (class_ → class)
    return `    ${wk}${pad} = ${val}`;
  });

  // node() call — include ... for containers
  const nodeCall = hasChildren
    ? `  node("shadcn:${exportName}", ..., props = list(\n${propLines.join(",\n")}\n  ))`
    : `  node("shadcn:${exportName}", props = list(\n${propLines.join(",\n")}\n  ))`;

  const lines = [``, ...docLines, sig];
  if (!hasChildren) lines.push(`  rlang::check_dots_empty()`);
  lines.push(nodeCall, `}`);
  return lines.join("\n");
}

// ── Insert into index.jsx (idempotent) ────────────────────────────────────────

function insertIntoIndex() {
  const indexPath = join(jsRoot, "src/index.jsx");
  let content = readFileSync(indexPath, "utf8");

  const importLine   = `import { ${exportName} } from "@/components/${name}";`;
  const registryLine = `  "shadcn:${exportName}": ${exportName},`;

  const alreadyImported    = content.includes(importLine);
  const alreadyRegistered  = content.includes(`"shadcn:${exportName}"`);

  if (alreadyImported && alreadyRegistered) {
    console.log(`  index.jsx       : already registered — skipped`);
    return;
  }

  if (!alreadyImported) {
    // Insert right before the blank line that precedes registerComponents
    content = content.replace(
      /\n\n(window\.shinyreact\.registerComponents)/,
      `\n${importLine}\n\n$1`,
    );
  }
  if (!alreadyRegistered) {
    // Insert as the last entry before });
    content = content.replace(/^(\}\);)$/m, `${registryLine}\n$1`);
  }

  // Both replacements are no-ops if index.jsx has drifted from the expected
  // shape. Verify the lines actually landed before claiming success — a silent
  // partial failure (registry entry without its import) only blows up at render.
  const importOk   = content.includes(importLine);
  const registerOk = content.includes(registryLine);
  if (!importOk || !registerOk) {
    const missing = [
      !importOk && "import line",
      !registerOk && "registry entry",
    ].filter(Boolean).join(" + ");
    throw new Error(
      `index.jsx: could not insert ${missing} for ${exportName}. ` +
      `The file does not match the expected shape (a blank line before ` +
      `window.shinyreact.registerComponents, and a "});" at column 0). ` +
      `Add the import and registry entry by hand, or fix the file shape.`,
    );
  }

  writeFileSync(indexPath, content);
  console.log(`  index.jsx       : ✓ added import + registry entry`);
}

// ── Append Python helper + regenerate re-exports (idempotent) ──────────────────

const pySrc = join(pkgRoot, "pkg-py/src/shinyshadcn");

function appendPython() {
  const modPath = join(pySrc, `_${category}.py`);
  let content = readFileSync(modPath, "utf8");

  if (content.match(new RegExp(`^def ${snake}\\(`, "m"))) {
    console.log(`  _${category}.py   : def ${snake}() already exists — skipped`);
  } else {
    writeFileSync(modPath, content.trimEnd() + "\n\n\n" + generatePython() + "\n");
    console.log(`  _${category}.py   : ✓ appended def ${snake}()`);
  }
  regenerateInit();
}

// Rebuild __init__.py from the public defs in each category module, so the new
// helper is imported and listed in __all__. Modules are ordered the way isort
// expects (alphabetical), so ruff stays quiet.
function regenerateInit() {
  const initPath = join(pySrc, "__init__.py");
  const entries = [
    { mod: "_dep", names: ["_dep"] },
    { mod: "_types", names: ["BadgeVariant", "ButtonSize", "ButtonVariant"] },
  ];
  for (const cat of CATEGORIES) {
    const text = readFileSync(join(pySrc, `_${cat}.py`), "utf8");
    const names = [...text.matchAll(/^def (\w+)\(/gm)].map((m) => m[1]).sort();
    if (names.length) entries.push({ mod: `_${cat}`, names });
  }
  entries.sort((a, b) => a.mod.localeCompare(b.mod));

  const lines = ['"""shadcn/ui components for shinyreact (Python helpers)."""', ""];
  const all = [];
  for (const { mod, names } of entries) {
    all.push(...names);
    const oneLine = `from .${mod} import ${names.join(", ")}`;
    if (oneLine.length <= 88) {
      lines.push(oneLine);
    } else {
      lines.push(`from .${mod} import (`, ...names.map((n) => `    ${n},`), ")");
    }
  }
  lines.push("", "__all__ = [", ...all.sort().map((n) => `    "${n}",`), "]");
  writeFileSync(initPath, lines.join("\n") + "\n");
  console.log(`  __init__.py     : ✓ regenerated re-exports (${all.length} names)`);
}

// ── Append R helper (idempotent) ──────────────────────────────────────────────

function appendR() {
  const rPath = join(pkgRoot, `pkg-r/R/${category}.R`);
  let content = readFileSync(rPath, "utf8");

  const fnName = `shadcn_${snake}`;
  if (content.includes(`${fnName} <-`)) {
    console.log(`  R/${category}.R   : ${fnName}() already exists — skipped`);
    return;
  }

  writeFileSync(rPath, content.trimEnd() + "\n" + generateR() + "\n");
  console.log(`  R/${category}.R   : ✓ appended ${fnName}()`);
}

// ── Run ───────────────────────────────────────────────────────────────────────

console.log(`\nFinalizing: ${name}  →  export ${exportName}  →  def ${snake}()\n`);
console.log(`  @shiny type=${ann.type} children=${ann.children ?? "false"}`);
console.log(`  props: ${props.map((p) => `${p.name}:${p.type}${p.rawDefault !== undefined ? "=" + p.rawDefault : ""}`).join("  ")}\n`);

insertIntoIndex();
appendPython();
appendR();

console.log(`
✓ Integration complete (category: ${category}).

Next:
  cd ui-frameworks/shadcn/js && npm run build
  Rscript -e 'roxygen2::roxygenise("ui-frameworks/shadcn/pkg-r")'   # refresh NAMESPACE + man/
  (then fill the TODO docstrings and test in an example app)
`);
