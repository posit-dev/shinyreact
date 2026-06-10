# ui-frameworks

Proof-of-concept UI component libraries built on top of shinyreact. Each subdirectory is a self-contained framework integration — its own JS bundle, Python helpers, and R helpers — that downstream Shiny apps can `source()` or `sys.path.insert` and use immediately.

This directory is not a published package. It exists to prototype what downstream framework packages look like before they graduate to their own repos.

---

## What's here

```
ui-frameworks/
  shadcn/        ← shadcn/ui components (Radix + Tailwind v4). 12 components, Python + R.
  mui/           ← Material UI scaffold. Directory structure ready; no components wrapped yet.
  updates.md     ← Changelog of structural decisions made during shadcn development.
  .claude/
    skills/
      scaffold-component.md   ← /scaffold-component skill: add one component to any framework
      scaffold-framework.md   ← /scaffold-framework skill: bootstrap a new framework from scratch
```

---

## Two models for wrapping a framework

**Copy-paste (shadcn model)** — component source is checked into `js/src/components/`. No npm dependency on the framework itself. You own the source and can trim TypeScript, adjust class names, and adapt to shinyreact's needs. Correct choice for shadcn, which is designed to be copied not installed.

**npm library (MUI model)** — component source stays in `node_modules`; Vite bundles it. Write thin wrapper files in `js/src/wrappers/`. Correct choice for MUI, Mantine, and any library not designed for copy-paste.

---

## Adding components or frameworks

Use the Claude skills in `.claude/skills/`:

- `/scaffold-component` — add one component to an existing framework (shadcn, mui, etc.)
- `/scaffold-framework` — bootstrap a new framework directory from scratch

---

## Shared conventions across all frameworks

- JS bundle: Vite IIFE, output to `www/<framework>.js`
- Externalize `react` → `window.shinyreact.React` and `react-dom/client` → `window.shinyreact.ReactDOM`
- Do **not** externalize `react-dom` — portal-based components (Radix overlays) need `createPortal` which only lives in `react-dom`, not `react-dom/client`
- Register via `window.shinyreact.registerComponents(null, { "framework:ComponentName": Fn })`
- Server props: `snake_case`. JS registration keys: `"framework:PascalCase"`.
- Import all hooks from a single `src/hooks.js` that destructures `window.shinyreact`
- Built assets (`www/`) are committed to the repo
