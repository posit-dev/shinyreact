# Validate `accordion` children are `accordion_panel` instances

**Date:** 2026-05-26
**Status:** Proposal — pending implementation plan
**Resolves:** #106

## Summary

`accordion.tagify()` unconditionally reads `.title`, `.children`, `._value`, and `.icon` on every entry in `self.children`, but `self.children: list[TagChild]` permits arbitrary non-`accordion_panel` values. Non-panel children produce an `AttributeError` at render time, far from where the bad child was added. Fix: validate at every entry point that places a child into an `accordion` (`__init__` positional args, `append()`, and a defense-in-depth check at the top of `tagify()`) and raise a clear `TypeError`. Apply identically to `shinyui.accordion` and `shinyuiclassonly.accordion`.

## Context

`accordion` and `accordion_panel` live in two sibling packages:

- `pkg-py/src/shinyui/_accordion.py` (full prototype — session-aware accessors, `update()`)
- `pkg-py/src/shinyuiclassonly/_accordion.py` (structure-only sibling — same `tagify()` strategy, no server-side machinery)

Both packages inherit child storage from `AllowsChildren` (`pkg-py/src/shinyui/_children.py`, `pkg-py/src/shinyuiclassonly/_children.py`):

```python
class AllowsChildren:
    children: list[TagChild]

    def __init__(self, *children: TagChild, **kwargs: Any) -> None:
        self.children = list(children)
        super().__init__(**kwargs)

    def append(self, child: TagChild) -> Self:
        self.children.append(child)
        return self
```

The Core overload of `accordion.__init__` declares `*args: accordion_panel`, but that's a static-typing hint only — at runtime `AllowsChildren.__init__` accepts anything assignable to `TagChild`. The Express form is worse: while `accordion(id="acc")` is the active parent, *any* value reaching `sys.displayhook` (a bare string, an htmltools `Tag`, another shinyui component) is routed to `accordion.append()`. The result is the bug documented in #106:

```python
with su.accordion(id="acc") as acc:
    "Some descriptive text"        # appended to acc.children
    with su.accordion_panel("Panel 1"):
        su.input_slider("n", "N", 1, 10, 5)

acc.tagify()  # AttributeError: 'str' object has no attribute 'title'
```

The four `# type: ignore[union-attr]` comments in `tagify()` are suppressing this exact runtime hazard, not just papering over a type-system limitation.

## Design

### Validation helper

A module-level helper in each `_accordion.py` file produces the canonical error message and keeps the three call sites in sync:

```python
def _check_panel(child: object) -> None:
    if not isinstance(child, accordion_panel):
        raise TypeError(
            f"accordion children must be accordion_panel instances, "
            f"got {type(child).__name__}"
        )
```

The message names the offending type but not the value. The traceback's call-site frame identifies *where* — that's the whole reason for validating at the entry points rather than at render.

### Entry points

Three sites place children into an `accordion`. All three validate.

**1. `__init__` (Core form, positional args).**

```python
def __init__(self, *args: accordion_panel, id: str, ...) -> None:
    for child in args:
        _check_panel(child)
    self._open = open
    # ...
    super().__init__(*args, id=id)
```

Catches the issue's second reproduction (`accordion("some text", accordion_panel(...), id="acc")`).

**2. `append()` (Express `with`-block displayhook path, plus any direct calls).**

```python
def append(self, child: TagChild) -> Self:
    _check_panel(child)
    return super().append(child)
```

Returns `self` via `super().append`, preserving the `AllowsChildren.append` signature. The `with`-block in the issue's first reproduction hits this path: `sys.displayhook("Some descriptive text")` → `dispatch_to_active_parent` → `acc.append("Some descriptive text")` → `TypeError` raised inside the `with` block, near the bad expression.

**3. `tagify()` (defense in depth).**

```python
def tagify(self) -> Tag:
    import shiny.ui as _sui

    for child in self.children:
        _check_panel(child)

    panels = [
        _sui.accordion_panel(
            child.title,
            *child.children,
            value=child._value,
            icon=child.icon,
        )
        for child in self.children
    ]
    # ...
```

Catches any path that bypasses `__init__` and `append` — most plausibly direct mutation like `acc.children.append("text")` or `acc.children[0] = "text"`. Also lets the panel-rebuilding comprehension drop its four `# type: ignore[union-attr]` suppressions: the explicit loop above narrows each `child` to `accordion_panel` for type checkers.

### Scope: both packages

`shinyui` and `shinyuiclassonly` carry the identical bug (same `tagify()` body, same `AllowsChildren`, same Express displayhook). Both get the same three-point validation and the same tests. Each package's `accordion_panel` import already exists in its `_accordion.py`, so the helper has the right class in scope.

### Out of scope

- **Narrowing children type via generics on `AllowsChildren`** (option 2 in #106). Would require a generic parameter or overridable child-type alias on the base mixin, rippling through every component. Worth doing later as a structural improvement; not needed to close this bug.
- **Auto-wrapping non-panel children** (option 3 in #106). Silently changes semantics — a bare string would become a panel with an empty title and an ambiguous `value`. Rejected.
- **Other components with similar exposure.** `card`, `accordion_panel` itself, and other `AllowsChildren` subclasses accept arbitrary `TagChild` deliberately. Only `accordion` requires children of a specific subclass (because `shiny.ui.accordion` does its own `isinstance(panel, AccordionPanel)` check on its positional args). No other component needs this validation today.

## Tests

Mirrored across `pkg-py/tests/shinyui/test_accordion.py` and `pkg-py/tests/shinyuiclassonly/test_accordion.py`. Six cases per package:

1. **`__init__` rejects non-panel positional args** — `accordion("text", id="acc")` raises `TypeError`. (Issue's Core reproduction.)
2. **`append()` rejects non-panel children** — `accordion(id="acc").append("text")` raises `TypeError`. (Direct call.)
3. **Express `with`-block rejects bare strings** — entering `with accordion(id="acc"):` then evaluating `"text"` via `sys.displayhook` raises `TypeError`. (Issue's Express reproduction; validates the displayhook → `append` path.)
4. **`tagify()` rejects mutated children** — construct a valid accordion, then `acc.children.append("text")`, then `acc.tagify()` raises `TypeError`. (Defense-in-depth path.)
5. **Error message names the offending type** — assert `"got str"` (or similar) is in the exception text.
6. **Well-formed accordions still render** — regression guard wrapping the existing `test_tagify_attribute_parity` shape, kept minimal since the existing test already covers the happy path.

For the Express case (test 3), use the same pattern as `tests/shinyui/test_ctx_stack.py` / `test_children.py` for invoking displayhook inside a `with` block.

## Cleanup

The four `# type: ignore[union-attr]` comments on `child.title`, `*child.children`, `value=child._value`, `icon=child.icon` in each `_accordion.py`'s `tagify()` are removed. The explicit `_check_panel` loop above the comprehension narrows the type for pyright.

## Risks

- **False positives.** A user wrapping `accordion_panel` in a subclass (`class MyPanel(accordion_panel): ...`) still passes `isinstance`. No false-positive surface here.
- **Behavior change for accidentally-working apps.** If any existing app silently appended non-panel children and got away with it (unlikely — the bug currently throws `AttributeError` at render), they will now see `TypeError` at insertion. The change converts a confusing late error into a clear early one; no app that previously rendered will stop rendering.
- **Both packages stay in lockstep.** The shared helper is duplicated rather than imported across packages — `shinyui` and `shinyuiclassonly` are deliberately independent. Tests in both packages guard against drift.
