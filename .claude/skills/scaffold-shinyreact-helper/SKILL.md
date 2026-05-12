---
name: scaffold-shinyreact-helper
description: Scaffold a new shinyreact downstream helper-package prototype with one stub component wired end-to-end. Use when starting a new helper package for a React UI library (e.g., shinymantine, shinyradix, shinyaggrid). Asks for the upstream package, short name, and target directory; renders templates with substitutions; verifies the scaffold builds, lints, tests, and serves HTTP 200.
---

# Scaffold a shinyreact helper package

## Overview

This skill produces a new helper-package prototype at a target directory. The output is **one stub component** wired end-to-end — the package author adds further components by following the established pattern (factory in Python + registered React component + entry-app wiring).

**Conventions enforced** (from [the helper-packages RFC](../../../docs/superpowers/specs/2026-05-12-downstream-helper-packages-rfc-design.md) §4):

- IIFE Vite bundle with React externalized to `window.shinyreact.React`
- Catalog keys namespaced as `<prefix>:<Component>`
- Python factory functions returning `shinyreact.Node(type="<prefix>:<Component>", props=...)`
- `HTMLDependency` produced by a `dep()` helper, consumed via `shinyreact.ui_output(id, extra_deps=[dep()])`
- Per-package directory layout: `js/` + `pkg-py/` + `example/`

## Non-goals

This skill targets the category-1 styled-component-library baseline. It does not auto-discover all components in the upstream library, configure theming, set up CI/publishing, or handle per-category divergences (headless, copy-paste, specialized). Those are added by the package author after scaffolding.

## How it works

The skill is fully self-contained. All file contents live as templates under `.claude/skills/scaffold-shinyreact-helper/templates/`, each using `{{placeholder}}` markers. The procedure: collect inputs → render each template with substitutions → write to the target directory → build and verify.

The rest of the procedure (inputs, substitution rules, scaffolding steps, verification) lands in subsequent tasks.

## Inputs

Before scaffolding, collect these from the user one at a time. Validate each before moving on.

1. **Short package name** (e.g., `mantine`, `radix`, `aggrid`). Lowercase, no separators, no `shiny` prefix — the skill prepends `shiny` to form the package name (e.g., `mantine` → `shinymantine`).
2. **Upstream npm package** that the helper will wrap (e.g., `@mantine/core`, `@radix-ui/react-dialog`, `ag-grid-react`). Used as a `dependencies` entry in the scaffold's `js/package.json`. (For now, a single package; multiple packages can be added by hand after scaffolding.)
3. **Catalog prefix** (defaults to the short package name). The string before `:` in catalog keys (e.g., `mantine` → `mantine:Button`).
4. **Stub component name** (defaults to `Button`). The single component the skill wires up end-to-end as proof the scaffold loads. The package author replaces or extends after scaffolding.
5. **Target directory** (defaults to `downstream-prototypes/shiny<name>/`). Where the scaffold lives.

After collecting all inputs, **echo them back to the user** and ask for confirmation before writing any files. Example:

> About to scaffold:
> - Package: `shinymantine` (at `downstream-prototypes/shinymantine/`)
> - Upstream: `@mantine/core`
> - Prefix: `mantine:`
> - Stub component: `Button`
>
> Proceed? (yes / change)

If they say "change", re-collect the affected input.

## Substitution rules

Templates under `templates/` use mustache-style `{{placeholder}}` markers. Substitute each occurrence with the corresponding value derived from the inputs:

| Placeholder | Derived from | Example (for `mantine`) |
|-------------|--------------|--------------------------|
| `{{name}}` | short package name (lowercase) | `mantine` |
| `{{pkg}}` | `shiny{{name}}` | `shinymantine` |
| `{{Name}}` | short name, capitalized | `Mantine` |
| `{{prefix}}` | catalog prefix | `mantine` |
| `{{Stub}}` | stub component name, PascalCase | `Button` |
| `{{stub}}` | stub component name, snake_case lowercase | `button` |
| `{{target_dir}}` | target directory | `downstream-prototypes/shinymantine` |
| `{{upstream_pkg}}` | upstream npm package | `@mantine/core` |

Substitution is plain textual replacement — no escaping, no conditional logic. If a template doesn't contain a placeholder, write it verbatim.
