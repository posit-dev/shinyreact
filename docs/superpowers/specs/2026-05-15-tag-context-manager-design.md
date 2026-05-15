# Tag as context manager — parent-stack via `sys.displayhook` + `ContextVar`

**Date:** 2026-05-15
**Status:** Design — Stage A prototype in `shinyreact`
**GitHub issue:** [posit-dev/shinyreact#70](https://github.com/posit-dev/shinyreact/issues/70)
**Umbrella:** [#68 — unified UI component class for Shiny Core and Express](https://github.com/posit-dev/shinyreact/issues/68)
**Builds on:** [#69 — metadata consolidation, merged in `ba858f4`](https://github.com/posit-dev/shinyreact/pull/100)
**Stage B target:** `rstudio/py-htmltools`

## Summary

Make `shinyui` components (and a thin `Tag` subclass) usable as context managers, so the Express idiom

```python
with card(id="main"):
    with accordion(id="acc"):
        with accordion_panel("A"):
            input_slider("n", "N", 1, 10, 5)
        with accordion_panel("B"):
            output_code("diag")
```

produces the same UI tree as the equivalent positional Core call. The mechanism is a lazily-installed `sys.displayhook` shim that reads a per-task `contextvars.ContextVar` parent stack. Entering any `AllowsChildren` component (or a `CtxTag`) pushes self onto the stack; the displayhook routes any bare-expression value to the stack tip via `htmltools.wrap_displayhook_handler`.

Stage A lives in `pkg-py/src/shinyui/`. Stage B (out of scope here) ports the `__enter__` / `__exit__` onto `htmltools.Tag` directly.

## Why this mechanism

Issue #70 originally framed two construction-time approaches: a `Tag` subclass that auto-appends in `__init__`, or a wrapper around `Tag` doing the same. Walking those through revealed three sharp edges that any construction-time approach inherits:

1. **Nested function calls pollute the wrong parent.** `with card(): accordion(panel("A"), panel("B"))` constructs the panels *before* the accordion claims them. Each panel sees the card on top of the stack and auto-appends to the card; the accordion then *also* takes them as its children. Net result: panels duplicated across two parents. A "steal back the children" fix in `AllowsChildren.__init__` is possible but brittle, especially when a component constructs auxiliary tags inside its own `__init__`.
2. **Bare literals slip past.** `with card(): "Hello"` discards the string. Construction-time hooks only intercept classes we control; plain `str`, `int`, `list[Tag]`, `MetadataNode`, etc. never call into our code, so they cannot be auto-appended. Express's displayhook approach captures them naturally because `wrap_displayhook_handler` coerces any `TagChild` value.
3. **Assigned-vs-bare cannot be distinguished at runtime.** `foo = h1("x")` triggers the same `__init__` as a bare `h1("x")`. Either both append (surprising side effect on a `foo =` line) or neither does.

The displayhook approach — already used by Shiny Express's `RecallContextManager` and by htmltools' own existing `Tag.__enter__` — does not have these problems: only *bare expression statements* trigger `sys.displayhook`, and the handler receives the fully-constructed value regardless of its type.

The cost is that `sys.displayhook` fires only in environments that actually display bare expressions:

- ✅ REPL / IPython / Jupyter
- ✅ Quarto Python cells (run via IPython)
- ✅ Shiny Express `app.py` (AST-rewritten by `expressify`)
- ✗ Plain `.py` script bodies — bare expressions are silently discarded by Python; user falls back to positional composition

This matches Express's current reach exactly. Shiny Core users already compose positionally; the `with` idiom is meaningfully available wherever Express's was, with no regression.

## Goals

- One set of `shinyui` component classes works in both positional (Core) and `with`-block (Express) form, producing identical UI trees.
- Per-task parent stack — two concurrent Shiny sessions in the same process do not cross-pollinate.
- `sys.displayhook` shim installed lazily, exactly once, with the previous displayhook preserved for fall-through (so REPL printing, Jupyter rendering, anything else built on displayhook keeps working).
- Validate the mechanics in `shinyreact` before proposing the change to `py-htmltools` upstream.

## Non-goals

- Refactoring Shiny Express's `RecallContextManager` to use this stack. Express's mechanism wraps function calls; ours hooks Tag/component instances. They coexist without interference and are left side by side for now.
- Making `with card(): h1("x")` work in plain Python script bodies without `expressify`. Not possible without AST rewriting, which is out of scope.
- Upstreaming `__enter__` / `__exit__` onto `htmltools.Tag`. That's Stage B.
- A new public-facing namespace of "ctx tags" matching every `htmltools.tags.*` method. `CtxTag` is provided as a minimal demonstration; the example app uses the existing `shinyui` classes.

## Architecture

### Module: `shinyui/_ctx_stack.py`

```python
from __future__ import annotations

import contextvars
import sys
from typing import Any, Callable

from htmltools import wrap_displayhook_handler

_stack: contextvars.ContextVar[tuple[Any, ...]] = contextvars.ContextVar(
    "shinyui_parent_stack", default=()
)
_installed: bool = False
_prev_displayhook: Callable[[object], None] | None = None


def _dispatch(x: object) -> None:
    stack = _stack.get()
    if stack:
        wrap_displayhook_handler(stack[-1].append)(x)
    else:
        assert _prev_displayhook is not None
        _prev_displayhook(x)


def _ensure_installed() -> None:
    global _installed, _prev_displayhook
    if not _installed:
        _prev_displayhook = sys.displayhook
        sys.displayhook = _dispatch
        _installed = True


def push(parent: Any) -> contextvars.Token[tuple[Any, ...]]:
    _ensure_installed()
    return _stack.set(_stack.get() + (parent,))


def pop(token: contextvars.Token[tuple[Any, ...]]) -> None:
    _stack.reset(token)


def dispatch_to_active_parent(x: Any) -> None:
    """Dispatch ``x`` to the current stack tip, if one exists.

    Called by ``AllowsChildren.__exit__`` after the token is reset so that
    nested ``with`` blocks propagate the finished component to its enclosing
    parent without touching the previous displayhook when no parent is active.
    """
    stack = _stack.get()
    if stack:
        wrap_displayhook_handler(stack[-1].append)(x)
```

Single-file module. Module-private functions; `push` / `pop` are imported by `_children.py` and `_ctx_tag.py`; `dispatch_to_active_parent` is imported by `_children.py` only. The `_installed` / `_prev_displayhook` globals are an intentional one-shot install — multiple `_ensure_installed()` calls are no-ops, so import order and test setup are unaffected.

`contextvars.ContextVar` (not `threading.local`) for asyncio compatibility — every `asyncio.Task` gets its own copy on creation; `Token`-based reset survives exceptions.

### Hook into `AllowsChildren`

Replace the existing no-op `__enter__` / `__exit__` in `shinyui/_children.py`.
`__enter__` pushes `self` onto the contextvar stack so that any bare expressions
inside the `with` body are routed to this component.  `__exit__` first pops `self`
off the stack (restoring the prior snapshot via the token), then — on normal exit —
calls `dispatch_to_active_parent(self)` so that the just-closed component is
automatically appended to whatever parent is still active.  This is what makes
nested `with` blocks compose: `with accordion():` inside `with card():` lands the
accordion in the card's children without any explicit call from the user.

> **Why `__exit__`-time dispatch is required.**  The `with X as y:` syntax never
> triggers `sys.displayhook` on `X` itself — `@expressify` only rewrites bare
> *expression statements* (`ast.Expr`), not `with`-headers.  So without the
> `dispatch_to_active_parent` call in `__exit__`, `with accordion()` inside
> `with card()` would silently vanish: the accordion would collect its own
> children correctly, but it would never end up in `card.children`.
> `htmltools.Tag.__exit__` solves the identical problem by calling
> `sys.displayhook(self)` after restoring its previous displayhook; our
> contextvar variant achieves the same effect via `dispatch_to_active_parent`,
> which reads the stack *after* the token reset so that self is routed to the
> outer parent, not back to itself.

```python
from ._ctx_stack import dispatch_to_active_parent, push, pop

class AllowsChildren:
    children: list[TagChild]

    def __init__(self, *children: TagChild, **kwargs: Any) -> None:
        self.children = list(children)
        super().__init__(**kwargs)

    def append(self, child: TagChild) -> Self:
        self.children.append(child)
        return self

    def __enter__(self) -> Self:
        self._ctx_token = push(self)
        return self

    def __exit__(self, *exc: object) -> None:
        pop(self._ctx_token)
        # If an enclosing ``with`` block is still active, dispatch self to it so
        # nested ``with`` blocks compose the same tree as positional calls.
        if exc[0] is None:  # no exception — normal exit
            dispatch_to_active_parent(self)
```

Three of the existing concrete classes (`card`, `accordion`, `accordion_panel`) already declare `AllowsChildren` and have Express overloads in place — they pick up `with`-block support with zero per-class changes.

`UiComponent.__enter__` (in `_base.py`) still raises for non-`AllowsChildren` components, so `with input_slider("n", ...)` produces the same clear `TypeError` it does today.

### `CtxTag` — plain-htmltools demonstration

Add `shinyui/_ctx_tag.py`:

```python
from __future__ import annotations

import contextvars
from typing import Any

from htmltools import Tag
from typing_extensions import Self

from ._ctx_stack import push, pop


class CtxTag(Tag):
    """`htmltools.Tag` subclass that pushes onto the shinyui parent stack on `__enter__`.

    Stage-A demonstration of the mechanism on a plain Tag (no Shiny dependency).
    Stage B (out of scope here) ports this behavior onto `Tag` itself upstream.

    Overrides `Tag.__enter__` / `__exit__` (which use a non-contextvar global
    `sys.displayhook` swap) with the async-safe contextvar variant. Outside a
    `with` block, behaves like `Tag`.
    """

    _ctx_token: contextvars.Token[tuple[Any, ...]]

    def __enter__(self) -> Self:
        self._ctx_token = push(self)
        return self

    def __exit__(self, *exc: object) -> None:
        pop(self._ctx_token)
```

Exported from `shinyui/__init__.py` for the standalone-htmltools test path (`with CtxTag("div") as d: CtxTag("h1", "x")`). The example app uses shinyui classes, not `CtxTag` directly — `CtxTag` exists to validate the mechanism on a vanilla `Tag` for the Stage B port.

## Data flow

```
with card(id="m") as c:           push(c)                      stack = (c,)
    "title"                       _dispatch("title")            wrap_displayhook_handler(c.append)("title")
    h1("hi") via CtxTag           _dispatch(h1)                 wrap_displayhook_handler(c.append)(h1)
    with accordion(id="a") as a:  push(a)                      stack = (c, a)
        accordion_panel("A")      _dispatch(panel)              wrap_displayhook_handler(a.append)(panel)
                                  pop(token_a)                  stack = (c,)
                                  dispatch_to_active_parent(a)  wrap_displayhook_handler(c.append)(a)
                                  pop(token_c)                  stack = ()
```

Each `__enter__` produces a `Token`; `__exit__` resets to the snapshot the token captured. Nested entries naturally form a stack because each token holds the *previous* contextvar value.

### Nested function-call interaction (the issue the user pinned earlier)

```python
with card(id="m") as c:
    accordion(
        accordion_panel("A", input_slider("n", "N", 1, 10, 5)),
        accordion_panel("B", output_code("diag")),
        id="a",
    )
```

Under (B), only the outermost `accordion(...)` is a bare expression statement. In Express/Jupyter/Quarto/REPL, Python invokes `sys.displayhook(accordion(...))` *after* the call has fully evaluated and the panels are already nested inside the accordion. The inner `accordion_panel(...)` and `input_slider(...)` calls are sub-expressions; they never reach `sys.displayhook`. The card sees only the final accordion. No pollution.

In a plain script body, the bare `accordion(...)` is silently discarded — same as today; user uses positional `card(accordion(...))` instead.

## Concurrency

Two `asyncio.Task`s, two Shiny sessions, each inside its own `with card():`. Because `ContextVar` copies on `asyncio.Task` creation, each task has an independent `_stack` value. The global `_dispatch` reads the current task's stack and routes to its tip. Tasks never see each other's parents.

`sys.displayhook` itself is process-global. The dispatch function is the single shared component, but it carries no state — its state-of-the-moment comes from the `ContextVar`. A non-shinyui caller (e.g. anything that calls `sys.displayhook(x)` directly while no `with` is active) sees the original previous displayhook via the fall-through branch.

## Public API

Exports added to `shinyui/__init__.py`:

- `CtxTag` — `htmltools.Tag` subclass with the `__enter__` / `__exit__` override. For Stage A demonstration and Stage B preview.

No other public additions — `AllowsChildren.__enter__` / `__exit__` were already part of the public surface; they just gained working bodies. `push` / `pop` and the `_ctx_stack` module are private.

## Interaction with existing mechanisms

- **htmltools' existing `Tag.__enter__` / `__exit__`.** These swap `sys.displayhook` globally without a contextvar. They remain on `Tag` itself; only `CtxTag` overrides them. The two mechanisms coexist — a user mixing plain `with htmltools.div():` and `with CtxTag("div"):` in the same process gets the existing htmltools behavior for the former and the new contextvar-aware behavior for the latter. We do not monkey-patch `Tag`.
- **Express's `RecallContextManager`.** Operates at the function-call layer (`ui.div(...)` returns an RCM, not a Tag). Our stack operates at the instance layer. The two never see each other's values: an RCM is not an `AllowsChildren`, and an `AllowsChildren` is not an RCM. If a user mixes Express's `ui.*` with shinyui's classes in one tree, each subtree uses its own collection mechanism. No code is required to make this work; it follows from the surfaces being disjoint.
- **`shinyui.UiComponent.__enter__`.** Still raises for non-`AllowsChildren` components, with the existing error message. Unchanged.

## Testing

Add `pkg-py/tests/test_ctx_stack.py`:

- `CtxTag` bare construction inside `with CtxTag("div") as d:` produces `d.children == [child]` (single nested `CtxTag`).
- Bare `str` inside `with CtxTag("div")` is appended via `wrap_displayhook_handler` (coerced to a text child).
- Bare `shinyui.input_slider(...)` inside `with card(...) as c:` is appended to `c.children`.
- Nested `with card(): with accordion(): accordion_panel(...)` produces the three-level tree with the panel as a child of the accordion only.
- `with card():` then `with card():` (sequential) — second card unaffected by first; stack fully popped between blocks.
- Two `asyncio.Task`s each running `async with card():` concurrently with `await asyncio.sleep(0)` between appends — each card has only its own children. Validates contextvar isolation.
- After all `with` blocks exit, `sys.displayhook` is the wrapped `_dispatch` (one-shot install) but calls with empty stack fall through to the original previous displayhook — verified by patching `sys.displayhook` before any shinyui import and confirming the original receives the value when no parent is active.
- `with input_slider("n", ...)` raises `TypeError` with the existing message (regression test that `UiComponent.__enter__` still wins for non-`AllowsChildren`).
- Snapshot test: rendering `card(accordion(accordion_panel("A", input_slider("n", "N", 1, 10, 5)), id="a"), id="m")` (Core form) and the equivalent `with card(id="m"): with accordion(id="a"): with accordion_panel("A"): input_slider("n", "N", 1, 10, 5)` (Express form, run inside an `expressify`'d helper) produce byte-identical HTML.

The Express-form snapshot is the headline acceptance test. Without `expressify` the bare-expression idiom doesn't fire displayhook; the test wraps the body in `@expressify` so the rewriting happens at definition time.

## Example app

New directory: `examples/app-py/15-shinyui-with-blocks/` (mirrors the numbering of the existing `14-unified-ui-prototype/` shinyui demo, which uses positional composition).

- `app.py` — a Shiny Express app whose UI tree is built entirely with `with card(): with accordion(): with accordion_panel(): ...` nesting, demonstrating the same components used in `14-unified-ui-prototype/` but in the `with`-block form. Exercises `input_slider` inside a panel, `output_code` driven by the slider, and `card.full_screen_value()` / `accordion.update(...)` on the server side.
- Brief README inline (top-of-file docstring) noting that this example demonstrates issue #70 and pointing to `14-unified-ui-prototype/` for the positional form so the two can be diffed side-by-side.

The example is the working demo the Stage A acceptance gate requires; it's also the manual sanity check that a real running Shiny session behaves correctly under the new mechanism.

## Risks & mitigations

- **Process-global `sys.displayhook` install.** Once installed, `_dispatch` stays as `sys.displayhook` for the life of the process. The fall-through branch preserves whatever was there before (so REPL / Jupyter still work). The install is one-shot so re-imports don't stack wrappers. If a third party swaps `sys.displayhook` *after* our install, our hook is lost — the user re-enters a `with` and would see no auto-append. Mitigation: `_ensure_installed()` runs on every `__enter__`, so we could detect `sys.displayhook is not _dispatch` and re-install. Decided against for Stage A simplicity — flag as an open question if it bites in practice.
- **Exception in `__exit__` after `_stack.reset` doesn't run.** `_stack.reset` is the first line of `__exit__`; the only way it doesn't run is if `__exit__` itself isn't called, which only happens on `with` statement protocol violation (rare; would be a Python bug). The `Token`-based reset is robust to body exceptions.
- **Contextvar token reused across tasks.** A `Token` is bound to the `ContextVar` and the context in which `set` was called. Using it from a different task raises `ValueError`. Mitigation: tokens are stored on the instance, and an `AllowsChildren` instance is normally entered once. If users hand the same instance to two tasks for concurrent `with` blocks, they get the explicit error.
- **`CtxTag` adds a path that diverges from `Tag` in subtle ways.** Stage A only overrides `__enter__` / `__exit__`; everything else is inherited. The Stage B port to `Tag` itself is the cleanup.

## Open questions (defer to implementation or follow-up)

- **Should `_ensure_installed()` re-install if `sys.displayhook` was swapped externally?** Adds a one-line guard. Defer until we see a real conflict.
- **Should the example also include a side-by-side Core-form comparison in the same file?** Likely yes — readers benefit from seeing the equivalence inline. Decide during implementation.
- **Stage B coordination with `htmltools.Tag.__enter__`.** Upstream port replaces the global-displayhook swap on `Tag` with this contextvar-aware variant; downstream callers (Express) keep working because their RCM path is independent. Out of scope for Stage A.

## Acceptance (Stage A)

- `with CtxTag("div") as d: CtxTag("h1", "x")` produces the expected children in a unit test.
- `with card(): with accordion(): accordion_panel("A", input_slider(...))` produces the same HTML as the positional Core form, confirmed by snapshot.
- Two concurrent `asyncio.Task`s each in their own `with card():` produce disjoint children (no cross-pollination).
- Example app runs and renders correctly in a Shiny Express session, with `input_slider` driving an `output_code` and an `accordion.update(...)` button working end-to-end.
- `with input_slider(...)` still raises the existing `TypeError`.

## Out-of-scope reminders

- Stage B (upstream port to `htmltools.Tag`).
- Refactoring Express's `RecallContextManager`.
- A general `ctx_tags` namespace mirroring `htmltools.tags.*`.
- Making the idiom work in plain `.py` script bodies without `expressify`.
