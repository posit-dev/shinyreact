# Bookmarking restoration implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore bookmarked input values into React state on page load by emitting a head `<script>` that the shinyreact JS bundle batch-applies into the input registry on init. Both `app.py` (`page_react`) and `ui.tsx` (`set_react_page`) patterns and both bookmark modes (URL, server-stored) work via the same path.

**Architecture:**
- **Python:** `page_react` and the page function installed by `set_react_page` call a new `_dep_page()` helper that returns `_dep()` plus an optional restore-script `<script>` (built by `_restore_script_tag()`) hoisted into `<head>` via `head_content()`.
- **JS:** `ensureShinyReactInitialized()` reads `window.shinyreact._restore`, batch-seeds entries into the input registry (without sending to Shiny), and replaces the global with a sentinel `{ "-applied": true, "-values": <appliedMap> }` for DevTools. The existing `useShinyInput` / `useSetShinyInput` / `useShinyInputValue` hooks pick up the seeded values via their existing registry-first lookup — no hook changes.

**Tech Stack:** Python (htmltools, Shiny `RestoreContext` API), TypeScript/React (vitest, jsdom), py-shiny Playwright fixtures, Vite/IIFE bundle.

**Spec:** `docs/superpowers/specs/2026-05-08-bookmarking-restoration-design.md` (#27).

---

## File structure

| Path | Status | Purpose |
|---|---|---|
| `pkg-py/src/shinyreact/_bookmark.py` | new | `_restore_script_tag()` + `_read_restore_input_values()` |
| `pkg-py/src/shinyreact/_output.py` | modify | add `_dep_page()` next to `_dep()` |
| `pkg-py/src/shinyreact/_page.py` | modify | `page_react` + `_react_page_fn` switch from `_dep()` → `_dep_page()` |
| `pkg-py/tests/test_bookmark_restore.py` | new | unit tests for the helper, `_dep_page`, and page wiring |
| `js/src/shiny-react/bookmark.ts` | new | `applyRestoredValues(registry)` |
| `js/src/shiny-react/use-shiny.ts` | modify | call `applyRestoredValues` from `ensureShinyReactInitialized()` |
| `js/src/index.ts` | modify | `window.shinyreact = Object.assign(window.shinyreact || {}, {...})` so it preserves `_restore` |
| `js/src/shiny-react/__tests__/use-shiny-restore.test.tsx` | new | unit tests |
| `pkg-py/src/shinyreact/www/shinyreact.js`, `js/dist/shinyreact.js` | regenerated | rebuilt via `make update-dist` |
| `examples/app-py/13-bookmarking/{app.py,bookmarking.js,styles.css,README.md}` | new | public example app |
| `pkg-py/tests/playwright/test_bookmark_restore.py` | new | py-shiny Playwright integration tests |
| `docs/features.md` | modify | add Bookmarking row |
| `docs/todos.md` | modify | remove the bookmarking entry |

---

### Task 1: Python — `_read_restore_input_values()` reads `RestoreContext.input` without consuming pending state

**Files:**
- Create: `pkg-py/src/shinyreact/_bookmark.py`
- Test: `pkg-py/tests/test_bookmark_restore.py`

- [ ] **Step 1: Write the failing test**

```python
# pkg-py/tests/test_bookmark_restore.py
from shiny.bookmark._restore_state import RestoreContext, RestoreInputSet
from shinyreact._bookmark import _read_restore_input_values


def test_read_restore_input_values_returns_underlying_dict() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello", "num": 42})
    assert _read_restore_input_values(ctx) == {"foo": "hello", "num": 42}


def test_read_restore_input_values_does_not_mark_pending() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    _read_restore_input_values(ctx)
    # No keys should be pending — we only inspected.
    assert ctx.input._pending == set()


def test_read_restore_input_values_empty() -> None:
    ctx = RestoreContext()
    # Default RestoreContext has empty RestoreInputSet
    assert _read_restore_input_values(ctx) == {}
```

- [ ] **Step 2: Run the tests and verify they fail**

```
uv run pytest pkg-py/tests/test_bookmark_restore.py -v
```
Expected: ImportError — `shinyreact._bookmark` does not exist.

- [ ] **Step 3: Implement the helper**

```python
# pkg-py/src/shinyreact/_bookmark.py
from __future__ import annotations

from shiny.bookmark._restore_state import RestoreContext


def _read_restore_input_values(ctx: RestoreContext) -> dict[str, object]:
    """Return the underlying input value map from a RestoreContext.

    Reads ``ctx.input.as_dict()`` directly. Does NOT call ``RestoreInputSet.get()``
    or the public ``restore_input(id, default)`` helper — those mark each value
    as pending and Shiny's normal flow would mark them used on the first flush,
    making the value unavailable to subsequent ``restore_input`` callers in the
    same render. We only want to *report* the values to the client; consumption
    semantics are unchanged.
    """
    return ctx.input.as_dict()
```

- [ ] **Step 4: Run the tests and verify they pass**

```
uv run pytest pkg-py/tests/test_bookmark_restore.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/src/shinyreact/_bookmark.py pkg-py/tests/test_bookmark_restore.py
git -c commit.gpgsign=false commit -m "feat(bookmark): add _read_restore_input_values helper"
```

---

### Task 2: Python — `_restore_script_tag()` returns `head_content` `<script>` or `None`

**Files:**
- Modify: `pkg-py/src/shinyreact/_bookmark.py`
- Test: `pkg-py/tests/test_bookmark_restore.py`

- [ ] **Step 1: Write the failing tests**

Append to `pkg-py/tests/test_bookmark_restore.py`:

```python
import json

from htmltools import HTMLDependency, TagList
from shiny.bookmark._restore_state import restore_context as restore_context_cm
from shinyreact._bookmark import _restore_script_tag


def _render_dep_to_head(dep: HTMLDependency) -> str:
    """Render an HTMLDependency to the HTML it would inject into <head>."""
    rendered = TagList(dep).tagify().render()
    head_html = "".join(d.as_html_tags() for d in rendered["dependencies"])
    return head_html + rendered["html"]


def test_restore_script_tag_no_context_returns_none() -> None:
    # No active RestoreContext at all.
    assert _restore_script_tag() is None


def test_restore_script_tag_empty_input_returns_none() -> None:
    ctx = RestoreContext()  # default: empty RestoreInputSet
    with restore_context_cm(ctx):
        assert _restore_script_tag() is None


def test_restore_script_tag_emits_head_content_with_json() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello", "num": 42})
    with restore_context_cm(ctx):
        dep = _restore_script_tag()

    assert dep is not None
    assert isinstance(dep, HTMLDependency)
    head_html = _render_dep_to_head(dep)
    # The script body sets window.shinyreact._restore via JSON.parse.
    assert "window.shinyreact" in head_html
    assert "_restore" in head_html
    # Round-trip the embedded JSON: extract the JSON.parse('...') argument.
    start = head_html.index("JSON.parse('") + len("JSON.parse('")
    end = head_html.index("')", start)
    parsed = json.loads(head_html[start:end])
    assert parsed == {"foo": "hello", "num": 42}


def test_restore_script_tag_escapes_closing_script_tag() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "</script><script>alert(1)</script>"})
    with restore_context_cm(ctx):
        dep = _restore_script_tag()
    assert dep is not None
    head_html = _render_dep_to_head(dep)
    # The literal "</script>" sequence inside the JSON payload must be escaped
    # so the browser does not see it as ending the script. The escaping replaces
    # "</" with "<\/", so no unescaped "</script" appears INSIDE the JSON.parse call.
    json_start = head_html.index("JSON.parse('")
    # Allow only ONE actual </script> (the one closing our injected tag).
    assert head_html.count("</script>") == 1
```

- [ ] **Step 2: Run the new tests and verify they fail**

```
uv run pytest pkg-py/tests/test_bookmark_restore.py -v -k "restore_script_tag"
```
Expected: ImportError on `_restore_script_tag`.

- [ ] **Step 3: Implement the helper**

Replace the contents of `pkg-py/src/shinyreact/_bookmark.py` with:

```python
from __future__ import annotations

import json

from htmltools import HTML, HTMLDependency, head_content, tags
from shiny.bookmark._restore_state import (
    RestoreContext,
    get_current_restore_context,
)


def _read_restore_input_values(ctx: RestoreContext) -> dict[str, object]:
    """Return the underlying input value map from a RestoreContext.

    Reads ``ctx.input.as_dict()`` directly. Does NOT call ``RestoreInputSet.get()``
    or the public ``restore_input(id, default)`` helper — those mark each value
    as pending and Shiny's normal flow would mark them used on the first flush,
    making the value unavailable to subsequent ``restore_input`` callers in the
    same render. We only want to *report* the values to the client; consumption
    semantics are unchanged.
    """
    return ctx.input.as_dict()


def _restore_script_tag() -> HTMLDependency | None:
    """Return a head-injected <script> carrying restored input values, or None.

    Reads the active Shiny ``RestoreContext`` set up during the HTTP request
    that loaded the page. Returns ``None`` when no bookmark query string was
    parsed or the context's input map is empty.

    SECURITY
    --------
    Bookmarked input values appear in the rendered HTML page source. In
    URL bookmark mode the values are also already in the URL itself, so this
    script adds no exposure. In server-stored bookmark mode (``?_state_id_=...``)
    the URL hides the values, but this script re-exposes them in the page
    source. Anything that can read the HTML — browser extensions, logging
    proxies, screen captures, "View Source" — can read these values. Apps must
    not put credentials, tokens, PII, or other sensitive data into inputs that
    participate in bookmarking.
    """
    ctx = get_current_restore_context()
    if ctx is None:
        return None
    values = _read_restore_input_values(ctx)
    if not values:
        return None

    # Escape "</" so the JSON cannot terminate the surrounding <script> tag.
    safe_json = json.dumps(values).replace("</", "<\\/")
    js = (
        "window.shinyreact = window.shinyreact || {};"
        f"window.shinyreact._restore = JSON.parse('{safe_json}');"
    )
    return head_content(tags.script(HTML(js)))
```

- [ ] **Step 4: Run the tests and verify they pass**

```
uv run pytest pkg-py/tests/test_bookmark_restore.py -v
```
Expected: all 7 passed.

- [ ] **Step 5: Add a "does not mark pending after emission" test**

Append to `pkg-py/tests/test_bookmark_restore.py`:

```python
def test_restore_script_tag_does_not_mark_pending() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        _restore_script_tag()
        # restore_input() inside the same context should still see "hello",
        # because _restore_script_tag did not mark "foo" as pending.
        from shiny.bookmark._restore_state import RestoreInputSet as _RIS  # noqa: F401
        from shiny.module import ResolvedId

        assert ctx.input.get(ResolvedId("foo")) == "hello"
```

- [ ] **Step 6: Run the test and verify it passes**

```
uv run pytest pkg-py/tests/test_bookmark_restore.py -v -k "does_not_mark_pending"
```
Expected: 2 passed (the original `_read_*` test and this new one).

- [ ] **Step 7: Commit**

```bash
git add pkg-py/src/shinyreact/_bookmark.py pkg-py/tests/test_bookmark_restore.py
git -c commit.gpgsign=false commit -m "feat(bookmark): add _restore_script_tag helper"
```

---

### Task 3: Python — `_dep_page()` wraps `_dep()` with the optional restore script

**Files:**
- Modify: `pkg-py/src/shinyreact/_output.py`
- Test: `pkg-py/tests/test_bookmark_restore.py`

- [ ] **Step 1: Write the failing tests**

Append to `pkg-py/tests/test_bookmark_restore.py`:

```python
from htmltools import HTMLDependency, TagList
from shinyreact._output import _dep, _dep_page


def test_dep_returns_htmldependency_only_no_context() -> None:
    result = _dep()
    assert isinstance(result, HTMLDependency)
    assert result.name == "shinyreact"


def test_dep_returns_htmldependency_only_with_context() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        result = _dep()
    # _dep() never wraps — it is the per-output helper.
    assert isinstance(result, HTMLDependency)


def test_dep_page_no_context_returns_htmldependency() -> None:
    result = _dep_page()
    assert isinstance(result, HTMLDependency)
    assert result.name == "shinyreact"


def test_dep_page_empty_context_returns_htmldependency() -> None:
    ctx = RestoreContext()  # active=False, empty input
    with restore_context_cm(ctx):
        result = _dep_page()
    assert isinstance(result, HTMLDependency)


def test_dep_page_with_active_context_returns_taglist() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        result = _dep_page()
    assert isinstance(result, TagList)
    # First child is the bundle dep; second is the head_content restore script.
    assert any(isinstance(c, HTMLDependency) and c.name == "shinyreact" for c in result)
```

- [ ] **Step 2: Run the new tests and verify they fail**

```
uv run pytest pkg-py/tests/test_bookmark_restore.py -v -k "dep"
```
Expected: ImportError — `_dep_page` does not exist.

- [ ] **Step 3: Add `_dep_page()` to `_output.py`**

Edit `pkg-py/src/shinyreact/_output.py` to add the import and helper. Final file should look like:

```python
from pathlib import Path
from typing import Sequence

from htmltools import HTMLDependency, Tag, TagChild, TagList, div

from ._bookmark import _restore_script_tag


def _dep() -> HTMLDependency:
    return HTMLDependency(
        name="shinyreact",
        version="0.1.0",
        source={"subdir": str(Path(__file__).parent / "www")},
        script={"src": "shinyreact.js", "defer": ""},
        stylesheet={"href": "shinyreact.css"},
    )


def _dep_page() -> TagChild:
    """Page-level shinyreact dependency: bundle + bookmark restore script.

    Use from page entry points (``page_react``, ``set_react_page``'s page
    function). Per-output consumers (``ui_output``) should keep calling
    ``_dep()`` — they do not carry page-level restore state.
    """
    restore = _restore_script_tag()  # may be None
    return TagList(_dep(), restore) if restore is not None else _dep()


def ui_output(id: str, extra_deps: Sequence[HTMLDependency] | None = None) -> Tag:
    """Create a Shiny output placeholder for a shinyreact renderer.

    Args:
        id: The output ID. Must match the server-side ``@shinyreact.reactive_output``
            function name.
        extra_deps: Additional HTML dependencies to include. Used by downstream
            packages to inject their own JS/CSS (e.g. ``shinyshadcn``).

    Returns:
        A ``<div>`` tag that the shinyreact Shiny output binding renders into.
    """
    return div(
        _dep(),
        *(extra_deps or []),
        id=id,
        class_="shinyreact-output",
    )
```

- [ ] **Step 4: Run the tests and verify they pass**

```
uv run pytest pkg-py/tests/test_bookmark_restore.py -v
```
Expected: all passed.

- [ ] **Step 5: Run the existing output/page test suites to confirm no regressions**

```
uv run pytest pkg-py/tests/test_output.py pkg-py/tests/test_page.py pkg-py/tests/test_set_react_page.py -v
```
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyreact/_output.py pkg-py/tests/test_bookmark_restore.py
git -c commit.gpgsign=false commit -m "feat(bookmark): add _dep_page() helper"
```

---

### Task 4: Python — switch `page_react` and `_react_page_fn` to `_dep_page()`

**Files:**
- Modify: `pkg-py/src/shinyreact/_page.py`
- Test: `pkg-py/tests/test_bookmark_restore.py`

- [ ] **Step 1: Write the failing tests**

Append to `pkg-py/tests/test_bookmark_restore.py`:

```python
from pathlib import Path

from shinyreact import page_react
from shinyreact._page import _build_react_page_fn


def _rendered_html(tag) -> str:
    rendered = tag.tagify().render()
    head_html = "".join(d.as_html_tags() for d in rendered["dependencies"])
    return head_html + rendered["html"]


def test_page_react_emits_restore_script_when_bookmark_active() -> None:
    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"txt": "hello"})
    with restore_context_cm(ctx):
        html = _rendered_html(page_react(title="t"))
    assert "window.shinyreact._restore" in html
    assert '"txt"' in html
    assert '"hello"' in html


def test_page_react_no_restore_script_without_bookmark() -> None:
    html = _rendered_html(page_react(title="t"))
    assert "window.shinyreact._restore" not in html


def test_set_react_page_emits_restore_script_when_bookmark_active(tmp_path: Path) -> None:
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")
    page_fn = _build_react_page_fn(index)

    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"a": 1})
    with restore_context_cm(ctx):
        html = _rendered_html(page_fn())
    assert "window.shinyreact._restore" in html
    assert '"a"' in html


def test_set_react_page_no_restore_script_without_bookmark(tmp_path: Path) -> None:
    index = tmp_path / "index.html"
    index.write_text("<div id='root'></div>")
    page_fn = _build_react_page_fn(index)
    html = _rendered_html(page_fn())
    assert "window.shinyreact._restore" not in html


def test_ui_output_does_not_emit_restore_script_when_bookmark_active() -> None:
    """ui_output uses _dep(), not _dep_page() — no restore script."""
    from shinyreact import ui_output

    ctx = RestoreContext()
    ctx.input = RestoreInputSet({"foo": "hello"})
    with restore_context_cm(ctx):
        html = _rendered_html(ui_output("main"))
    assert "window.shinyreact._restore" not in html
```

- [ ] **Step 2: Run the new tests and verify they fail**

```
uv run pytest pkg-py/tests/test_bookmark_restore.py -v -k "emits_restore_script or no_restore_script or ui_output_does_not"
```
Expected: the `emits_restore_script` cases fail because `page_react` and `_build_react_page_fn` still call `_dep()`. The `no_restore_script` and `ui_output` cases may pass already.

- [ ] **Step 3: Switch the page entry points to `_dep_page()`**

Edit `pkg-py/src/shinyreact/_page.py`:

Change the import on line 11 from:
```python
from ._output import _dep
```
to:
```python
from ._output import _dep, _dep_page
```

Inside `page_react` (around line 66), change:
```python
return page_bare(
    _dep(),
    tags.div(id="root"),
    *args,
    title=title,
    lang=lang,
)
```
to:
```python
return page_bare(
    _dep_page(),
    tags.div(id="root"),
    *args,
    title=title,
    lang=lang,
)
```

Inside `_build_react_page_fn`'s inner `_react_page_fn` (around line 217), change:
```python
return cast(Tag, TagList(_dep(), *deps, HTML(index_html)))
```
to:
```python
return cast(Tag, TagList(_dep_page(), *deps, HTML(index_html)))
```

- [ ] **Step 4: Run the new tests and verify they pass**

```
uv run pytest pkg-py/tests/test_bookmark_restore.py -v
```
Expected: all green.

- [ ] **Step 5: Run all Python tests to confirm no regressions**

```
make py-check-tests
```
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add pkg-py/src/shinyreact/_page.py pkg-py/tests/test_bookmark_restore.py
git -c commit.gpgsign=false commit -m "feat(bookmark): wire page_react and set_react_page through _dep_page()"
```

---

### Task 5: JS — `applyRestoredValues()` helper in `bookmark.ts`

**Files:**
- Create: `js/src/shiny-react/bookmark.ts`
- Create: `js/src/shiny-react/__tests__/use-shiny-restore.test.tsx`

- [ ] **Step 1: Inspect existing test conventions**

Skim `js/src/shiny-react/__tests__/input-registry.test.ts` to confirm the vitest+vi.mock setup. New tests follow the same conventions.

- [ ] **Step 2: Write the failing tests**

Create `js/src/shiny-react/__tests__/use-shiny-restore.test.tsx`:

```ts
/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, expect, it, beforeEach, vi } from "vitest";

vi.mock("../get-shiny", () => ({
  getShiny: vi.fn(() => undefined),
}));

import { InputRegistry } from "../input-registry";
import { applyRestoredValues } from "../bookmark";

declare global {
  // eslint-disable-next-line no-var
  var window: any;
}

function freshWindow(): void {
  // jsdom provides window; clear any prior shinyreact state.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (globalThis as any).window = (globalThis as any).window || {};
  delete (globalThis as any).window.shinyreact;
}

describe("applyRestoredValues", () => {
  beforeEach(() => {
    freshWindow();
  });

  it("seeds registry entries from window.shinyreact._restore and replaces it with sentinel", () => {
    (window as any).shinyreact = { _restore: { foo: "hello", num: 42 } };
    const registry = new InputRegistry();

    applyRestoredValues(registry);

    expect(registry.get<string>("foo")?.getValue()).toBe("hello");
    expect(registry.get<number>("num")?.getValue()).toBe(42);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": { foo: "hello", num: 42 },
    });
  });

  it("with no _restore set, leaves registry empty and writes empty sentinel", () => {
    (window as any).shinyreact = {};
    const registry = new InputRegistry();

    applyRestoredValues(registry);

    expect(registry.size()).toBe(0);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": {},
    });
  });

  it("with no window.shinyreact at all, creates the namespace and writes sentinel", () => {
    const registry = new InputRegistry();
    applyRestoredValues(registry);
    expect((window as any).shinyreact._restore).toEqual({
      "-applied": true,
      "-values": {},
    });
  });

  it("re-running does not clobber the -values snapshot", () => {
    (window as any).shinyreact = { _restore: { foo: "hello" } };
    const registry = new InputRegistry();

    applyRestoredValues(registry);
    const firstValues = (window as any).shinyreact._restore["-values"];
    applyRestoredValues(registry);
    const secondValues = (window as any).shinyreact._restore["-values"];

    expect(secondValues).toEqual(firstValues);
    expect(secondValues).toEqual({ foo: "hello" });
  });

  it("does not call shiny setInputValue (uses add, not setValue)", () => {
    (window as any).shinyreact = { _restore: { foo: "hello" } };
    const registry = new InputRegistry();
    const entry = vi.spyOn(registry, "add");

    applyRestoredValues(registry);

    // We use add() so the value is stored without invoking
    // shinySetInputValueDebounced. The first useShinyInput mount will
    // re-broadcast through setValue() at the existing path.
    expect(entry).toHaveBeenCalledWith("foo", "hello");
  });

  it("drains pendingSubscribers when seeding via add()", () => {
    (window as any).shinyreact = { _restore: { foo: "hello" } };
    const registry = new InputRegistry();
    const subscriber = vi.fn();
    // Subscribe before the producer adds — should queue in pendingSubscribers.
    const unsub = registry.subscribe<string>("foo", subscriber);

    applyRestoredValues(registry);

    expect(subscriber).toHaveBeenCalledWith("hello");
    unsub();
  });
});
```

- [ ] **Step 3: Run the tests and verify they fail**

```
cd js && npx vitest run src/shiny-react/__tests__/use-shiny-restore.test.tsx
```
Expected: cannot resolve `../bookmark`.

- [ ] **Step 4: Implement `bookmark.ts`**

Create `js/src/shiny-react/bookmark.ts`:

```ts
/* eslint-disable @typescript-eslint/no-explicit-any */
import { type InputRegistry } from "./input-registry";

/**
 * Adopt bookmarked input values into the input registry.
 *
 * Reads `window.shinyreact._restore` (set by a head <script> emitted by
 * Python's `_restore_script_tag`), seeds each entry into `registry` via
 * `add()` so the value is stored without sending to Shiny, and replaces
 * the global with a sentinel `{ "-applied": true, "-values": <appliedMap> }`
 * for DevTools inspection.
 *
 * Idempotent: when called against an already-applied global (the sentinel's
 * "-applied" key is true), it does not re-apply and preserves the snapshot.
 *
 * SECURITY: bookmarked input values arrive in the page HTML source. URL mode
 * already exposes them in the URL; server-stored mode re-exposes them via
 * this script. Apps must not put credentials, tokens, PII, or other
 * sensitive data into inputs that participate in bookmarking.
 */
export function applyRestoredValues(registry: InputRegistry): void {
  const win = (typeof window !== "undefined" ? window : (globalThis as any)) as any;
  const ns = (win.shinyreact = win.shinyreact || {});
  const restore = ns._restore;

  const applied: Record<string, unknown> = {};
  if (restore && typeof restore === "object" && !restore["-applied"]) {
    for (const [id, value] of Object.entries(restore)) {
      registry.add(id, value);
      applied[id] = value;
    }
    ns._restore = { "-applied": true, "-values": applied };
    return;
  }

  if (restore && typeof restore === "object" && restore["-applied"]) {
    // Already applied — preserve the existing snapshot.
    return;
  }

  // No restore data at all — establish the uniform post-init sentinel.
  ns._restore = { "-applied": true, "-values": {} };
}
```

- [ ] **Step 5: Run the tests and verify they pass**

```
cd js && npx vitest run src/shiny-react/__tests__/use-shiny-restore.test.tsx
```
Expected: 6 passed.

- [ ] **Step 6: Run JS lint**

```
make js-lint
```
Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add js/src/shiny-react/bookmark.ts js/src/shiny-react/__tests__/use-shiny-restore.test.tsx
git -c commit.gpgsign=false commit -m "feat(bookmark): add applyRestoredValues helper"
```

---

### Task 6: JS — call `applyRestoredValues` from `ensureShinyReactInitialized`, and stop `index.ts` from clobbering `_restore`

**Files:**
- Modify: `js/src/shiny-react/use-shiny.ts`
- Modify: `js/src/index.ts`
- Modify: `js/src/shiny-react/__tests__/use-shiny-restore.test.tsx`

- [ ] **Step 1: Write the failing test for `useShinyInput` adopting restored values**

Append to `js/src/shiny-react/__tests__/use-shiny-restore.test.tsx`:

```tsx
import * as React from "react";
import { act, render } from "@testing-library/react";
import { useShinyInput } from "../use-shiny";
import { getReactRegistry } from "../react-registry";

// Force `useShinyInitialized` to flip to true synchronously for these tests.
vi.mock("../lifecycle-store", () => {
  let initialized = true;
  return {
    subscribeLifecycle: (cb: () => void) => {
      initialized = true;
      cb();
      return () => {};
    },
    getInitializedSnapshot: () => initialized,
    getBusySnapshot: () => false,
  };
});

function Probe({ id, defVal }: { id: string; defVal: string }) {
  const [v] = useShinyInput<string>(id, defVal);
  return <span data-testid="v">{v}</span>;
}

describe("useShinyInput + restore", () => {
  beforeEach(() => {
    freshWindow();
    // Reset the singleton react registry between tests.
    const reg = getReactRegistry();
    Array.from(reg.inputs.keys()).forEach((k) => reg.inputs.remove(k));
  });

  it("adopts a restored value as initial render value, ignoring defaultValue", () => {
    (window as any).shinyreact = { _restore: { foo: "hello" } };

    let utils!: ReturnType<typeof render>;
    act(() => {
      utils = render(<Probe id="foo" defVal="default" />);
    });

    expect(utils.getByTestId("v").textContent).toBe("hello");
  });

  it("uses defaultValue when no restore data is present", () => {
    (window as any).shinyreact = {};

    let utils!: ReturnType<typeof render>;
    act(() => {
      utils = render(<Probe id="bar" defVal="default" />);
    });

    expect(utils.getByTestId("v").textContent).toBe("default");
  });

  it("namespaced ids: _restore = {'ns-foo': 'hello'} is adopted by useShinyInput('foo', _, {namespace:'ns'})", () => {
    (window as any).shinyreact = { _restore: { "ns-foo": "hello" } };

    function NsProbe() {
      const [v] = useShinyInput<string>("foo", "default", { namespace: "ns" });
      return <span data-testid="v">{v}</span>;
    }

    let utils!: ReturnType<typeof render>;
    act(() => {
      utils = render(<NsProbe />);
    });

    expect(utils.getByTestId("v").textContent).toBe("hello");
  });
});
```

- [ ] **Step 2: Run the new tests and verify they fail**

```
cd js && npx vitest run src/shiny-react/__tests__/use-shiny-restore.test.tsx
```
Expected: the three new cases fail because `ensureShinyReactInitialized()` does not yet call `applyRestoredValues`.

- [ ] **Step 3: Wire `applyRestoredValues` into `ensureShinyReactInitialized`**

Edit `js/src/shiny-react/use-shiny.ts`:

Add an import near the top of the file (next to the other relative imports):
```ts
import { applyRestoredValues } from "./bookmark";
```

Replace the `ensureShinyReactInitialized` function (currently at the bottom of the file) with:

```ts
let shinyReactInitialized = false;
function ensureShinyReactInitialized() {
  if (shinyReactInitialized) {
    return;
  }

  initializeReactRegistry();
  // Adopt any bookmark-restored input values BEFORE the output binding
  // begins consuming server messages, so the registry already holds the
  // restored values by the first useShinyInput mount.
  applyRestoredValues(getReactRegistry().inputs);
  createReactOutputBinding();
  initializeMessageRegistry();

  shinyReactInitialized = true;
}
```

- [ ] **Step 4: Make the bundle preserve `_restore`**

Edit `js/src/index.ts` lines 58–76. Currently:

```ts
window.shinyreact = {
  registerComponents,
  ...
  React,
  ReactDOM,
};
```

Change to:

```ts
// Preserve any pre-bundle assignment (e.g. window.shinyreact._restore set
// by the head <script> emitted from Python's _restore_script_tag).
window.shinyreact = Object.assign(window.shinyreact || {}, {
  registerComponents,
  useSetShinyInput,
  useShinyBusy,
  useShinyInput,
  useShinyInputValue,
  useShinyOutputStatus,
  useShinyOutputValue,
  useShinyMessageHandler,
  useShinyInitialized,
  ImageOutput,
  MISSING,
  ShinyModuleProvider,
  ShinyReactComponentElement,
  ShinyOutput,
  React,
  ReactDOM,
});
```

- [ ] **Step 5: Run the JS tests and verify they pass**

```
cd js && npx vitest run
```
Expected: all green, including the new restore tests.

- [ ] **Step 6: Run JS lint**

```
make js-lint
```
Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add js/src/shiny-react/use-shiny.ts js/src/index.ts js/src/shiny-react/__tests__/use-shiny-restore.test.tsx
git -c commit.gpgsign=false commit -m "feat(bookmark): adopt restored values during shinyreact init"
```

---

### Task 7: Rebuild bundle and copy into Python package

**Files:**
- Regenerate: `js/dist/shinyreact.js`, `pkg-py/src/shinyreact/www/shinyreact.js`

- [ ] **Step 1: Run the dist build**

```
make update-dist
```
Expected: builds the JS bundle and copies into `pkg-py/src/shinyreact/www/` (and `pkg-r/inst/lib/shiny/`).

- [ ] **Step 2: Confirm both copies updated**

```
ls -l js/dist/shinyreact.js pkg-py/src/shinyreact/www/shinyreact.js
```
Expected: both have a recent mtime.

- [ ] **Step 3: Commit the regenerated bundle**

```bash
git add js/dist/ pkg-py/src/shinyreact/www/
git -c commit.gpgsign=false commit -m "chore: rebuild shinyreact bundle for bookmark restoration"
```

---

### Task 8: Public example app — `examples/app-py/13-bookmarking/`

**Files:**
- Create: `examples/app-py/13-bookmarking/app.py`
- Create: `examples/app-py/13-bookmarking/bookmarking.js`
- Create: `examples/app-py/13-bookmarking/styles.css`
- Create: `examples/app-py/13-bookmarking/README.md`

- [ ] **Step 1: Verify `13` is the next free directory**

```
ls examples/app-py/
```
If `13-bookmarking` already exists, pick the next free number and use it everywhere below.

- [ ] **Step 2: Create the styles file**

Create `examples/app-py/13-bookmarking/styles.css`:

```css
body { font-family: system-ui, sans-serif; padding: 24px; max-width: 720px; }
.card { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
label { display: block; margin-bottom: 4px; font-weight: 600; }
input[type=text], input[type=number] { width: 100%; padding: 6px; }
.row { display: flex; gap: 16px; align-items: center; }
.output { color: #555; font-family: monospace; }
button { padding: 8px 16px; cursor: pointer; }
.note { font-size: 0.875rem; color: #666; }
```

- [ ] **Step 3: Create the React client (no-build JS)**

Create `examples/app-py/13-bookmarking/bookmarking.js`:

```js
// Bookmarking example — demonstrates RestoreContext flowing into React inputs.
(function () {
  var React = window.shinyreact.React;
  var h = React.createElement;
  var useShinyInput = window.shinyreact.useShinyInput;
  var useShinyOutputValue = window.shinyreact.useShinyOutputValue;
  var useSetShinyInput = window.shinyreact.useSetShinyInput;

  function App() {
    var txt = useShinyInput("txt", "");
    var num = useShinyInput("num", 0);
    var chk = useShinyInput("chk", false);
    var bookmarkClicks = useSetShinyInput("bookmark_clicks", 0, {
      debounceMs: 0,
      priority: "event",
    });
    var greeting = useShinyOutputValue("greeting", "");
    var clickCount = React.useRef(0);

    function handleBookmark() {
      clickCount.current += 1;
      bookmarkClicks(clickCount.current);
    }

    return h(
      "div",
      null,
      h("h1", null, "Bookmarking demo"),
      h(
        "p",
        { className: "note" },
        "Edit the inputs, click 'Bookmark', then copy the URL and open it in a new tab.",
      ),
      h(
        "div",
        { className: "card" },
        h("label", null, "Text"),
        h("input", {
          type: "text",
          value: txt[0],
          onChange: function (e) {
            txt[1](e.target.value);
          },
        }),
      ),
      h(
        "div",
        { className: "card" },
        h("label", null, "Number"),
        h("input", {
          type: "number",
          value: num[0],
          onChange: function (e) {
            num[1](Number(e.target.value));
          },
        }),
      ),
      h(
        "div",
        { className: "card" },
        h("label", null, "Checkbox"),
        h("input", {
          type: "checkbox",
          checked: chk[0],
          onChange: function (e) {
            chk[1](e.target.checked);
          },
        }),
      ),
      h(
        "div",
        { className: "card" },
        h("div", { className: "output" }, "Server says: ", greeting),
      ),
      h("button", { onClick: handleBookmark, "data-testid": "bookmark-btn" }, "Bookmark"),
    );
  }

  var registry = { App: App };
  window.shinyreact.registerComponents({}, registry);

  var root = window.shinyreact.ReactDOM.createRoot(document.getElementById("root"));
  root.render(h(App));
})();
```

- [ ] **Step 4: Create the Shiny app**

Create `examples/app-py/13-bookmarking/app.py`:

```python
from pathlib import Path

import shinyreact
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session, reactive

_src_dir = Path(__file__).parent
_dep = HTMLDependency(
    name="bookmarking-example",
    version=str(int((_src_dir / "bookmarking.js").stat().st_mtime)),
    source={"subdir": str(_src_dir)},
    script={"src": "bookmarking.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)


def app_ui(request):
    # page_react picks up the active RestoreContext (if any) and emits the
    # restore <script> tag automatically via _dep_page().
    return shinyreact.page_react(_dep, title="shinyreact bookmarking")


def server(input: Inputs, output: Outputs, session: Session):
    @shinyreact.reactive_output
    def greeting() -> str:
        chk_label = "yes" if input.chk() else "no"
        return f"text={input.txt()!r} num={input.num()} checked={chk_label}"

    @reactive.effect
    @reactive.event(input.bookmark_clicks, ignore_init=True)
    async def _on_bookmark_click() -> None:
        await session.bookmark()


app = App(app_ui, server, bookmark_store="url")
```

- [ ] **Step 5: Create the README**

Create `examples/app-py/13-bookmarking/README.md`:

```markdown
# 13-bookmarking

Demonstrates bookmark restoration in shinyreact:

- `page_react()` (via `_dep_page()`) emits a `<script>` in `<head>` carrying the
  restored input values when Shiny parses a bookmark query string.
- The shinyreact bundle batch-seeds the input registry on init, so
  `useShinyInput` returns the restored value as its initial render value.

## Try it

```
shiny run examples/app-py/13-bookmarking/app.py
```

1. Change the text, number, and checkbox.
2. Click **Bookmark** — the URL changes to include the inputs as a query
   string.
3. Copy the URL into a new tab — the inputs initialise from the URL.

## Bookmark modes

This example uses `bookmark_store="url"`, which encodes inputs into the URL
itself. Switch the call to `bookmark_store="server"` to test the
server-stored variant; the same restoration mechanism applies.

> **Security:** bookmarked input values appear in the rendered HTML page
> source. Do not place credentials, tokens, or PII into inputs that
> participate in bookmarking.
```

- [ ] **Step 6: Smoke-test the example app**

```
uv run shiny run examples/app-py/13-bookmarking/app.py --port 8765 &
sleep 2
curl -s "http://127.0.0.1:8765/?_inputs_&txt=%22hi%22&num=7&chk=true" | grep -c "_restore"
kill %1 2>/dev/null
```
Expected: a positive count (script tag appears in the rendered HTML when query string is a bookmark).

If the curl test reports zero, inspect the HTML manually — the example may need adjustments to the input ids or the test URL.

- [ ] **Step 7: Commit**

```bash
git add examples/app-py/13-bookmarking/
git -c commit.gpgsign=false commit -m "feat(examples): add 13-bookmarking demo"
```

---

### Task 9: Playwright integration tests using py-shiny

**Files:**
- Create: `pkg-py/tests/playwright/__init__.py` (if the directory does not exist)
- Create: `pkg-py/tests/playwright/test_bookmark_restore.py`

- [ ] **Step 1: Confirm py-shiny Playwright fixtures are available**

```
uv run python -c "from shiny.playwright import controller; from shiny.pytest import create_app_fixture; print('ok')"
```
Expected: prints `ok`.

If imports fail, install playwright extras: `uv sync --extra playwright` (or whichever group the project uses) and re-run.

- [ ] **Step 2: Confirm or create the playwright tests directory**

```
ls pkg-py/tests/playwright/ 2>/dev/null || mkdir -p pkg-py/tests/playwright
[ -f pkg-py/tests/playwright/__init__.py ] || touch pkg-py/tests/playwright/__init__.py
```

- [ ] **Step 3: Write the Playwright tests**

Create `pkg-py/tests/playwright/test_bookmark_restore.py`:

```python
"""End-to-end bookmark restoration tests against the 13-bookmarking example.

Each test launches the example app via py-shiny's app fixture, navigates to a
bookmark URL, waits for Shiny to initialise, and asserts the React-rendered
DOM reflects the restored input values.
"""

from pathlib import Path
from urllib.parse import urlencode

import pytest
from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture

EXAMPLE_APP = Path(__file__).resolve().parents[2] / "../examples/app-py/13-bookmarking/app.py"

app = create_app_fixture(EXAMPLE_APP.resolve())


def _wait_for_shiny_initialized(page: Page) -> None:
    page.wait_for_function(
        "window.Shiny && window.Shiny.initializedPromise"
    )
    page.evaluate("window.Shiny.initializedPromise")


def test_url_mode_restores_inputs(page: Page, app) -> None:
    qs = "_inputs_&" + urlencode({"txt": '"hello"', "num": "42", "chk": "true"})
    page.goto(f"{app.url}?{qs}")
    _wait_for_shiny_initialized(page)

    expect(page.locator('input[type=text]')).to_have_value("hello")
    expect(page.locator('input[type=number]')).to_have_value("42")
    expect(page.locator('input[type=checkbox]')).to_be_checked()
    expect(page.locator(".output")).to_contain_text("text='hello'")
    expect(page.locator(".output")).to_contain_text("num=42")
    expect(page.locator(".output")).to_contain_text("checked=yes")


def test_no_bookmark_renders_defaults(page: Page, app) -> None:
    page.goto(app.url)
    _wait_for_shiny_initialized(page)

    expect(page.locator('input[type=text]')).to_have_value("")
    sentinel = page.evaluate("JSON.stringify(window.shinyreact._restore)")
    assert sentinel == '{"-applied":true,"-values":{}}'


def test_server_mode_restores_inputs(page: Page, tmp_path: Path) -> None:
    """Round-trip server-stored bookmarking through the app's bookmark button."""
    # Build a fresh fixture for a server-mode variant of the app. We use the
    # existing example with a runtime monkey-patch via the fixture factory.
    server_app = create_app_fixture(EXAMPLE_APP.resolve(), bookmark_store="server")
    with server_app() as live:
        page.goto(live.url)
        _wait_for_shiny_initialized(page)

        page.locator('input[type=text]').fill("server-hello")
        page.locator('input[type=number]').fill("99")
        page.locator('input[type=checkbox]').check()

        page.locator('[data-testid="bookmark-btn"]').click()
        # The bookmark handler updates the URL — wait for the state_id query.
        page.wait_for_url("**?_state_id_=*")
        bookmarked_url = page.url

        # Reload from a clean state.
        page.goto("about:blank")
        page.goto(bookmarked_url)
        _wait_for_shiny_initialized(page)

        expect(page.locator('input[type=text]')).to_have_value("server-hello")
        expect(page.locator('input[type=number]')).to_have_value("99")
        expect(page.locator('input[type=checkbox]')).to_be_checked()
```

> **Note:** the exact `create_app_fixture` argument names (`bookmark_store=`),
> the `app.url` accessor, and how to spawn a second fixture mid-test depend on
> the py-shiny pytest API in use. If the API differs from what's shown above,
> consult `from shiny.pytest import create_app_fixture` source and adapt
> accordingly — the structure of the test (URL navigation, assertions) stays
> the same.

- [ ] **Step 4: Run the Playwright tests**

```
uv run pytest pkg-py/tests/playwright/test_bookmark_restore.py -v
```
Expected: all pass. If the `create_app_fixture` API does not accept
`bookmark_store=`, simplify `test_server_mode_restores_inputs` to skip with a
clear message and move it to follow-up work.

- [ ] **Step 5: Commit**

```bash
git add pkg-py/tests/playwright/
git -c commit.gpgsign=false commit -m "test(bookmark): add Playwright e2e for url + server restore"
```

---

### Task 10: Documentation updates

**Files:**
- Modify: `docs/features.md`
- Modify: `docs/todos.md`

- [ ] **Step 1: Update `docs/features.md`**

Open `docs/features.md` and add a row to the relevant feature table for "Bookmark restoration" — describe in one line that input values from `?_inputs_&...` and `?_state_id_=...` URLs are restored automatically into `useShinyInput` initial values, and link the new example.

- [ ] **Step 2: Update `docs/todos.md`**

Open `docs/todos.md` and remove the "Bookmarking and initial state" entry (or replace it with a pointer to the new follow-up issue for the custom-value channel + save-side helper if you intend to track that). Do not leave a "shipped on date" note — git history is the record.

- [ ] **Step 3: Commit**

```bash
git add docs/features.md docs/todos.md
git -c commit.gpgsign=false commit -m "docs: mention bookmark restoration in features; clear from todos"
```

---

### Task 11: Final integration check

- [ ] **Step 1: Run the full Python check**

```
make py-check
```
Expected: format, types, and tests all pass.

- [ ] **Step 2: Run the full JS check**

```
make js-lint
cd js && npx vitest run
```
Expected: no lint errors, all tests pass.

- [ ] **Step 3: Verify the example loads with a real bookmark URL**

```
uv run shiny run examples/app-py/13-bookmarking/app.py --port 8765 &
sleep 2
curl -s "http://127.0.0.1:8765/?_inputs_&txt=%22hello%22&num=42" > /tmp/page.html
grep -F 'window.shinyreact._restore' /tmp/page.html
kill %1 2>/dev/null
```
Expected: the grep matches at least one line.

- [ ] **Step 4: PR description**

When opening the PR, the description should:

- Reference issue #27 with `Closes #27`.
- Note the deferred follow-up (full Playwright integration may require a separate issue depending on harness scope — file it now if the harness needed adjustments). Suggested wording: "Follow-up: file an issue for end-to-end browser tests if the py-shiny Playwright harness needs framework changes; this PR includes per-mode tests that exercise the live flow."

---

## Spec self-review

Cross-check this plan against `docs/superpowers/specs/2026-05-08-bookmarking-restoration-design.md`:

| Spec section | Tasks covering it |
|---|---|
| Mechanism (HTML script, `window.shinyreact._restore`) | T2 (emission), T5/T6 (consumption) |
| Why HTML over websocket | informational; design captured in spec |
| Underscore prefix and stability | T2 docstring, T5 helper docstring |
| JS-side adoption (batch + sentinel) | T5, T6 |
| Python emission (`_restore_script_tag`) | T1, T2 |
| Wiring via `_dep_page()` | T3, T4 |
| Order guarantee (head + non-defer vs defer bundle) | T2 (`head_content` use), T6 (bundle preserves `_restore` via `Object.assign`) |
| Security comments at three sites | T2 docstring, T5 docstring, T8 README |
| Python unit tests #1–#13 | T1, T2, T3, T4 |
| JS unit tests #1–#7 | T5 (1, 2, 3, 6), T6 (4, 5, 7) |
| Playwright integration | T9 |
| Public example | T8 |
| Files affected list | All matched. |

No gaps detected.
