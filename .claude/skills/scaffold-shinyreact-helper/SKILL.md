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
