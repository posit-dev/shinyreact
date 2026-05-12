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

## Procedure

Run these steps in order. After each step, briefly confirm to the user what landed. Do not commit the scaffold — leave that to the package author.

### Step 1: Create the directory layout

```bash
mkdir -p {{target_dir}}/js/src/components
mkdir -p {{target_dir}}/pkg-py/src/{{pkg}}/www
mkdir -p {{target_dir}}/pkg-py/tests
mkdir -p {{target_dir}}/example
```

### Step 2: Render templates

For each template under `.claude/skills/scaffold-shinyreact-helper/templates/`, read the file, perform every substitution from the table in the "Substitution rules" section above, and write to the corresponding location in `{{target_dir}}`. The mapping:

| Template | Destination |
|----------|-------------|
| `templates/README.md.tpl` | `{{target_dir}}/README.md` |
| `templates/js/package.json.tpl` | `{{target_dir}}/js/package.json` |
| `templates/js/tsconfig.json.tpl` | `{{target_dir}}/js/tsconfig.json` |
| `templates/js/vite.config.ts.tpl` | `{{target_dir}}/js/vite.config.ts` |
| `templates/js/.gitignore.tpl` | `{{target_dir}}/js/.gitignore` |
| `templates/js/src/types.ts.tpl` | `{{target_dir}}/js/src/types.ts` |
| `templates/js/src/index.ts.tpl` | `{{target_dir}}/js/src/index.ts` |
| `templates/js/src/components/Stub.tsx.tpl` | `{{target_dir}}/js/src/components/{{Stub}}.tsx` |
| `templates/pkg-py/pyproject.toml.tpl` | `{{target_dir}}/pkg-py/pyproject.toml` |
| `templates/pkg-py/src/__init__.py.tpl` | `{{target_dir}}/pkg-py/src/{{pkg}}/__init__.py` |
| `templates/pkg-py/src/_dep.py.tpl` | `{{target_dir}}/pkg-py/src/{{pkg}}/_dep.py` |
| `templates/pkg-py/src/_components.py.tpl` | `{{target_dir}}/pkg-py/src/{{pkg}}/_components.py` |
| `templates/pkg-py/tests/test_factories.py.tpl` | `{{target_dir}}/pkg-py/tests/test_factories.py` |
| `templates/example/app.py.tpl` | `{{target_dir}}/example/app.py` |

Also touch the placeholder for the empty `www/` directory:

```bash
touch {{target_dir}}/pkg-py/src/{{pkg}}/www/.gitkeep
```

### Step 3: Install JS dependencies

```bash
cd {{target_dir}}/js && npm install
```

Wait for completion (1-3 minutes for a typical UI library). If `npm install` warns about peer-dependency conflicts (e.g., `@mui/icons-material` requiring a different `@mui/material` major), surface the warning to the user — they may need to pin the upstream package version more tightly. Do not auto-fix.

For styled-component libraries that need emotion (MUI, Mantine), the user may need to add these themselves after scaffolding:

```bash
cd {{target_dir}}/js && npm install @emotion/react @emotion/styled
```

Mention this if and only if the upstream package is in the MUI/Mantine family.

### Step 4: Build the bundle

```bash
cd {{target_dir}}/js && npm run build
```

Expected: writes `{{target_dir}}/js/dist/{{pkg}}.js`. If the build fails because the upstream package isn't actually used in the stub (the stub uses a plain `<button>`), the build should still succeed because the import is only declared in `package.json`, not referenced in source. The user replaces the stub's plain button with the upstream component as their first manual edit.

### Step 5: Lint

```bash
cd {{target_dir}}/js && npm run lint
```

Expected: exits 0 with no output. If lint fails, surface the error verbatim.

### Step 6: Copy bundle to Python package www/

```bash
cp {{target_dir}}/js/dist/{{pkg}}.js {{target_dir}}/pkg-py/src/{{pkg}}/www/{{pkg}}.js
```

### Step 7: Install the Python package as editable

```bash
uv pip install -e {{target_dir}}/pkg-py
```

If this fails (the prototype shinymui hit this; in sandboxed environments `uv pip` may panic), try these fallbacks in order:

```bash
# Fallback 1: use venv pip directly
.venv/bin/pip install -e {{target_dir}}/pkg-py

# Fallback 2: venv Python with pip module
.venv/bin/python -m pip install -e {{target_dir}}/pkg-py
```

If all pip-based installs fail (e.g., pip is not installed in the uv-managed venv), you can manually create the editable install by adding a `.pth` file:

```bash
SITE=$(python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null \
  || .venv/bin/python -c "import site; print(site.getsitepackages()[0])")
echo "{{target_dir}}/pkg-py/src" > "$SITE/_editable_impl_{{pkg}}.pth"
```

Verify the install succeeded with:
```bash
.venv/bin/python -c "import {{pkg}}; print('{{pkg}} ok')"
```

### Step 8: Run the factory test

```bash
cd {{target_dir}}/pkg-py && uv run python -m pytest tests/test_factories.py -v
```

Or fall back to `.venv/bin/python -m pytest tests/test_factories.py -v` if `uv run` has venv-resolution issues.

Expected: `1 passed` (the stub factory test).

### Step 9: Programmatic smoke test

Start the example app, verify HTTP 200 + bundle loads, then stop. Use a port unlikely to collide (8765 is the convention used by the shinymui prototype's smoke tests).

```bash
# Start the app (fall back to .venv/bin/python -m shiny run if uv run panics)
uv run shiny run --port 8765 {{target_dir}}/example/app.py &
# OR: .venv/bin/python -m shiny run --port 8765 {{target_dir}}/example/app.py &
SHINY_PID=$!
sleep 4

# Page returns 200
curl -s -o /tmp/scaffold_smoke.html -w "%{http_code}\n" http://localhost:8765/

# HTML references the bundle URL with the right name
grep -c "{{pkg}}-" /tmp/scaffold_smoke.html

# Bundle URL itself returns 200
# Note: Shiny renders src="lib/..." (no leading slash) — strip the leading / from the pattern
BUNDLE_URL=$(grep -oE 'lib/{{pkg}}-[^"]+/{{pkg}}\.js' /tmp/scaffold_smoke.html | head -1)
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8765/$BUNDLE_URL"

# Cleanup
kill $SHINY_PID 2>/dev/null || true
pkill -f "shiny run --port 8765" 2>/dev/null || true
```

Expected outputs:
- First curl: `200`
- grep count: at least `1`
- Second curl: `200`

If any of these fail, surface the failure to the user and stop. Common causes: port 8765 in use (try 8766), `shinyreact` not installed in the venv, bundle copy failed.

### Step 10: Final summary

Report back to the user:

- Number of files created (count by walking `{{target_dir}}`)
- Bundle size from `ls -lh {{target_dir}}/js/dist/{{pkg}}.js`
- All verifications that passed (build, lint, factory test, HTTP 200, bundle 200)
- **Next steps for the package author:**
  - Edit `{{target_dir}}/js/src/components/{{Stub}}.tsx` to use the real `{{upstream_pkg}}` component instead of the plain `<button>`
  - Add more factories in `{{target_dir}}/pkg-py/src/{{pkg}}/_components.py` following the pattern
  - Add tests in `{{target_dir}}/pkg-py/tests/test_factories.py` for each new factory
  - For styled-component libraries: install peer deps like `@emotion/react @emotion/styled`
  - Reference `downstream-prototypes/shinymui/` for examples of more complex patterns (children/composition, server-pushed data via `useShinyOutputValue`)
  - When ready to commit: `git add {{target_dir}}/` then commit with a descriptive message

Do **not** commit the scaffold — leave that decision to the package author.
