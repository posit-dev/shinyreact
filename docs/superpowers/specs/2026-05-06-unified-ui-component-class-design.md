# Unified UI component class for Shiny Core and Express

**Date:** 2026-05-06
**Status:** Design — umbrella issue; prototype to be built in `shinyreact` before upstream adoption
**Prototype repo:** `posit-dev/shinyreact` (this repo) — playground for the design
**Upstream targets (post-acceptance):** `posit-dev/py-shiny` (issues 1 & 2), `rstudio/py-htmltools` (issue 3)
**Related notes:** `_dev/notes-regular-and-express.md` in `py-shiny`

## Summary

Replace the current "function returns `Tag`" UI surface with a class-per-component model. Each UI component becomes a `Tagifiable` Python class that owns its own metadata (children, HTML dependencies, input handler, bookmark serializer, `update()` method). The existing `ui.card(...)`, `ui.input_slider(...)` call sites stay the same — they become thin factory functions that return instances. The new class is also exposed (`ui.UiCard`, `ui.UiInputSlider`) for type hints and `isinstance` checks.

This work proceeds in two stages:

- **Stage A — prototype in `shinyreact`.** Build the class hierarchy and a small set of reference component classes here, where the surface area is small and the audience is friendly. Validate the API ergonomics, the Core/Express overload story, the bookmark/handler lifecycle, and the Tag-as-context-manager idea against a couple of real components. Iterate freely; breaking changes are cheap.
- **Stage B — upstream adoption in `py-shiny` / `py-htmltools`.** Once the team accepts the design, the patterns are ported upstream: the class hierarchy and lifecycle into `py-shiny`'s `ui` module (covering every existing `ui.input_*` and layout); the Tag-as-context-manager change into `py-htmltools` proper.

The umbrella tracks three independently-shippable child issues, each with a Stage A and Stage B target:

1. **Metadata consolidation** — `UiComponent` / `UiInput` / `AllowsChildren` plus reference component classes. (Stage A: `shinyreact`. Stage B: `py-shiny`.)
2. **Core/Express unification** — single overloaded signature per class that works inline and as a context manager. (Stage A: `shinyreact`. Stage B: `py-shiny`. Depends on issue 1.)
3. **Tag as context manager** — `__enter__` / `__exit__` plus a parent-tag context stack on `Tag`. (Stage A: prototyped via a `Tag` subclass / wrapper inside `shinyreact`. Stage B: `py-htmltools`. Independent.)

## Motivation

Three pain points the current design cannot fix without architectural change:

- **Per-component metadata is fragmented.** A date input's input handler is registered in `_input_handler.py`, its bookmark serializer is in `bookmark/_serializers.py`, its UI factory is in `ui/_input_date.py`, and its update function is `update_date_input` in yet another module. Adding a new input requires touching four files; the relationships between them are implicit.
- **Core and Express need different code paths today.** Express uses `RecallContextManager` to convert top-level function calls inside a `with` block into children of an enclosing layout. Core needs the children passed positionally. Today the two paths are different functions with different rules; users learn two mental models.
- **`Tag` is not a context manager.** The Express ergonomic win — `with ui.div(): ui.h1("x")` reading top-to-bottom — is implemented via Express-specific machinery and only works inside Express. The same idiom outside Express (or in a hybrid Core app that wants Express-style nesting in one place) does not work.

A class-per-component model addresses all three: one file per component owns its full lifecycle, the class can declare both inline and context-manager signatures via overloads, and the underlying `Tag` returned by `tagify()` can itself participate in a generic context-manager protocol.

`shinyreact` is the right venue for the prototype. It already ships a small, isolated UI surface with a fast iteration loop and no entrenched user base, so the cost of trying a design and walking it back is low. `py-shiny` is the wrong place to discover that an API doesn't feel right — every change there is a public commitment.

## Goals

- Every UI component is a `Tagifiable` class with a clear inheritance position.
- Existing `ui.card(...)`, `ui.input_slider(...)` call sites continue to work without edits at the upstream stage. Return type changes from `Tag` to the component class.
- Per-component metadata (handler, serializer, deps, update method) lives on the class.
- Core and Express modes share a single user-facing symbol per component.
- Components that can hold children opt into the capability via a mixin; components that cannot (e.g. slider) raise a clear error if used as a context manager.
- The design is validated in `shinyreact` against working examples before being proposed upstream.
- Each child issue lands independently at its respective upstream repo and provides value on its own.

## Non-goals

- Replacing `Tag` itself or restructuring htmltools' core data model.
- Changing the wire protocol or any client-side JavaScript.
- Adding new UI components or capabilities. This is a refactor of how existing components are expressed.
- Changing the input-handler registry's call shape (handlers still resolve by name on the wire).
- Bringing pure HTML helpers (`tags.*`, `HTML(...)`, `markdown(...)`, `tooltip(...)`) into the class hierarchy. They stay as plain `Tag`-returning functions.
- Bringing server-triggered functions (`modal_show`, `notification_show`, `insert_ui`, `Progress`) into the class hierarchy. They are imperative server APIs, not renderable UI.
- R package equivalent. Out of scope; a follow-up if the Python design proves out.

## Class hierarchy

Three sibling categories under `UiComponent`, distinguished by their server-side concern:

```
UiComponent                     # base: tagify(), html_dependencies, default __enter__ that raises
  ├── UiInput                   # adds: id, input_handler_name, bookmark_serializer (class default), update()
  │     └── UiInputSlider, UiInputText, UiInputDate, UiInputSelect, UiInputActionButton, ...
  ├── UiOutput                  # adds: id (no input handler, no bookmark serializer; consumes @render.* values)
  │     └── UiOutputText, UiOutputCode, UiOutputPlot, UiOutputUi, UiOutputDataFrame, ...
  └── UiLayout                  # container category; no id (most have AllowsChildren). Pages live here too.
        └── UiCard, UiSidebar, UiAccordion, UiNavPanel, UiLayoutColumns, UiCardHeader, UiToolbar, UiValueBox,
            UiPageFluid, UiPageFixed, UiPageFillable, UiPageBootstrap, UiPageAuto, UiPageSidebar, UiPageNavbar, ...
```

Pages (`page_*`) are `UiLayout, AllowsChildren` like any other container. Their special properties — `theme=`, `title=`, `window_title=`, non-nestability — are kwargs and per-class concerns, not a category-level distinction worth a separate base class.

`AllowsChildren` is **orthogonal** to the category split. It's an opt-in mixin that any concrete leaf class adds to its base list when (and only when) it accepts positional children:

| Concrete class                         | Bases                                  |
|----------------------------------------|----------------------------------------|
| `UiInputSlider`, `UiInputSelect`, ...  | `UiInput`                              |
| `UiOutputCode`, `UiOutputText`, ...    | `UiOutput`                             |
| `UiCard`, `UiSidebar`, ...             | `UiLayout, AllowsChildren`             |
| `UiPageFluid`, `UiPageNavbar`, ...     | `UiLayout, AllowsChildren`             |
| (hypothetical childless layout)        | `UiLayout`                             |
| (hypothetical input wanting children)  | `UiInput, AllowsChildren`              |

The rule is: **you can `with X(...)` if and only if `X` declares `AllowsChildren` in its bases.** No category-level assumption.

Today the practical fallout is:
- All current inputs are `UiInput`-only (no `AllowsChildren`).
- All current outputs are `UiOutput`-only (no `AllowsChildren`).
- All current layouts (including pages) are `UiLayout, AllowsChildren`. The design does not assume future layouts must be — a childless variant is expressible.

`AllowsChildren` provides:

- `children: list[TagChild]`
- `__enter__(self) -> Self` — pushes self onto the parent-tag stack, returns self.
- `__exit__(self, *exc)` — pops the stack.
- `append(self, child: TagChild)`.

`UiComponent.__enter__` is defined and **raises** with a message naming the component and explaining that it does not accept children. This gives a clear error instead of `AttributeError: __enter__`. `AllowsChildren.__enter__` overrides this. So `with ui.input_slider(...):`, `with ui.output_code(...):`, and any childless layout/page all raise the same clear error.

### Components that straddle categories

A handful of components are *both* inputs and containers — most notably `navset_*` (the active tab name is `input.<id>()`, and the navset holds child `nav_panel`s) and `accordion` (has `update_accordion()` for its `id`, holds child panels). These declare both bases:

```python
class UiNavsetTab(UiInput, AllowsChildren):
    """Holds nav_panel children; produces input.<id>() with the active tab name."""
    input_handler_name = "shiny.navset"
    ...

class UiAccordion(UiInput, AllowsChildren):
    """Holds accordion_panel children; produces input.<id>() with the open panel set."""
    ...
```

Multiple inheritance is intentional and confined to genuine cross-cutting cases. The MRO discipline noted in **Risks** below keeps this manageable: `AllowsChildren` is a strict mixin (no `__init__` cooperation needed), so adding it to any base is safe.

### What is *not* in the hierarchy

These exist in `py-shiny` but do not become `UiComponent` subclasses:

- **Server-triggered functions** — `modal_show`, `notification_show`, `show_toast`, `insert_ui`, `remove_ui`, `Progress`. They are imperative server-side functions with side effects, not renderable UI. The fragments they accept (`modal(...)`, `toast(...)`) *are* `UiLayout, AllowsChildren`.
- **Pure HTML helpers** — `tags.*`, `HTML(...)`, `markdown(...)`, `tooltip(...)`, `popover(...)`, `help_text(...)`. They construct `Tag`s with no Shiny lifecycle (no id, no handler, no render target). They stay as plain functions returning `Tag`. The hierarchy is reserved for components with Shiny semantics.
- **Configuration objects** — `Theme`, brand.yml integration, `SidebarOptions`, `NavbarOptions`, `fill.*` helpers, busy-indicator helpers. These are passed *to* components as kwargs; they are not components themselves.

## Public API shape: function-as-factory

Each component exposes two public symbols:

```python
# ui/_card.py

class UiCard(UiLayout, AllowsChildren):
    """Public class: data + tagify() + update()."""
    def __init__(self, *args, full_screen: bool = False, ...): ...
    def tagify(self) -> Tag: ...

def card(*args, full_screen: bool = False, ...) -> UiCard:
    """Public factory. Validates, normalizes, returns UiCard."""
    return UiCard(*args, full_screen=full_screen, ...)
```

Why both symbols:

- `ui.card(...)` is the primary user-facing API. The function signature is where overloads, validation, normalization, and any deprecation shims live.
- `ui.UiCard` is the public class for type hints (`def f(c: UiCard)`), `isinstance` checks, and subclassing.
- `__init__` stays minimal so tests and advanced users can construct instances directly without re-running validation.

The cost is two signatures to keep in sync per component. In practice the function forwards `*args, **kwargs` to the class for the common case; pyright catches drift.

## Lifecycle decisions

The first two rows below are **`UiInput`-specific** — outputs and layouts have neither input handlers nor bookmark serializers. The remaining rows apply to every `UiComponent` subclass.

| Concern | Decision |
|---|---|
| Input handler (the function) — `UiInput` only | Stays in the global `input_handlers` registry. Class declares `input_handler_name: ClassVar[str]`. Registration happens at module import time via an explicit call near the class definition (no `__init_subclass__` magic). |
| Bookmark serializer — `UiInput` only | `ClassVar` default on the class; per-instance attribute override. Session-side bookmark machinery looks up the serializer by walking from input id → component instance → its serializer (see open question below). |
| HTML dependencies | `ClassVar` on the class. Resolved at `tagify()` time. |
| `update()` session handling — `UiInput` only | Session captured at `__init__` if `get_current_session()` returns one; otherwise looked up at `update()` call time via `get_current_session()`. Explicit `session=` kwarg always wins. |
| `tagify()` | Pure, deterministic, side-effect-free. Safe to call multiple times — the renderer may invoke it more than once for a single instance. |
| `__enter__` registration into Express collection — `AllowsChildren` only | Pushes onto a parent-tag context stack (introduced by issue 3). Express's existing `RecallContextManager` either delegates to this stack or is replaced by it (see open question). |

## Sub-issue 1: metadata consolidation

### Stage A — prototype in `shinyreact`

**Scope.** Introduce `UiComponent`, `UiInput`, `UiOutput`, `UiLayout`, `AllowsChildren` in `shinyreact`. Build a small set of reference component classes — enough to exercise each archetype:

- One simple input (no children, no nested config): e.g. `UiInputSlider`.
- One input with structured configuration: e.g. `UiInputSelect` (`choices` dict, including optgroups). Validates that complex inputs work with the class model without using `AllowsChildren`.
- One output: e.g. `UiOutputCode`. Validates that `UiOutput` is meaningfully different from `UiInput` (no handler, no bookmark serializer) and from `UiLayout` (no children).
- One layout with children: e.g. `UiCard`. Validates `UiLayout, AllowsChildren`.
- One straddling component: e.g. `UiAccordion` (or a minimal `UiNavsetTab`). Validates that multiple inheritance from `UiInput, AllowsChildren` works — handler registration, bookmark serialization, child collection, and `update()` all coexist on one class.

For each, implement: `__init__`, `tagify()`, `html_dependencies`, and (for inputs) `input_handler_name`, `bookmark_serializer`, `update()`. Add factory functions (`input_slider(...)`, `card(...)`) that return instances. Demonstrate end-to-end use in a `shinyreact` example app, including a bookmark round-trip and an `instance.update(...)` call from the server.

**Acceptance (Stage A).**

- Reference classes exist with full lifecycle (handler, serializer, deps, update).
- Example app demonstrates each archetype in a real Shiny session.
- Bookmark round-trip works for the prototyped input(s).
- The hierarchy and the `AllowsChildren` mixin work as designed; trying to use a non-`AllowsChildren` class as a context manager raises a clear error.
- Snapshot test confirms `tagify()` output matches the equivalent `py-shiny` output for the same inputs (sanity check that we haven't drifted from upstream rendering).

### Stage B — upstream adoption in `py-shiny`

**Scope.** Port the validated hierarchy into `py-shiny`. Migrate every existing `ui.input_*` and layout factory onto the new classes. Move existing factory function bodies into `tagify()`. Wire up `update()` methods on input classes; existing `update_input_*` module-level functions become deprecated shims that delegate to `instance.update(...)`.

**Acceptance (Stage B).**

- Every existing `ui.input_*` and layout factory has a corresponding class, exported alongside the function.
- `ui.input_slider("n", ...)` returns `UiInputSlider`, embeds anywhere a `Tag` did, renders identically (existing snapshot tests pass unchanged).
- Bookmark round-trips for every input still work end-to-end. The internal lookup path may change (id → class instance → serializer); the user-visible behavior does not.
- All existing `update_input_*` calls still work. Equivalent `instance.update(...)` works.
- No behavior change for end users in either Core or Express mode.

**Out of scope for this issue (both stages).** Express auto-context-manager-ization of arbitrary components; Tag-as-context-manager. Layouts gain `AllowsChildren` but their Express usage continues to go through `RecallContextManager` for now.

## Sub-issue 2: Core/Express unification (depends on issue 1)

### Stage A — prototype in `shinyreact`

**Scope.** Add overloaded `__init__` signatures to the reference component classes so the same `card(...)` symbol type-checks correctly in both Core (`card(child_a, child_b, full_screen=True)`) and Express (`with card(full_screen=True): ...`) usage. Surface clear runtime errors when the modes are mixed.

**Acceptance (Stage A).**

- `card(*args, ...)` and `with card(...):` both type-check on the reference classes, with mode-appropriate docstrings shown by IDEs.
- Express mode is the first overload (so IDEs prefer it where signatures collide).
- Mixing modes (e.g. `with card(child, ...):`) raises with a clear message.
- An example app demonstrates the same component used in both modes within the same project.

### Stage B — upstream adoption in `py-shiny`

**Scope.** Apply the validated overload pattern to every `py-shiny` component class introduced in issue 1, Stage B.

**Acceptance (Stage B).**

- Every component class has the dual overload.
- Express usage continues to render the same children in the same order as today.
- IDE behavior (Pyright, Pylance) confirmed in both modes.

**Out of scope (both stages).** Generalizing the mechanism to all `Tag`s — that's issue 3.

## Sub-issue 3: Tag as context manager (independent)

### Stage A — prototype in `shinyreact`

**Scope.** Prototype the parent-tag context stack within `shinyreact`. Two viable approaches:

- A `Tag` subclass (`CtxTag` or similar) exported from `shinyreact` that adds `__enter__` / `__exit__` and uses a contextvar stack. Used in the reference component classes' `tagify()` outputs.
- A wrapper class that holds a `Tag` and provides the context-manager surface around it.

Either way, the goal is to validate the contextvar mechanics, the interaction with `Tagifiable`, and the user-facing ergonomics before proposing the change to upstream htmltools.

**Acceptance (Stage A).**

- `with shinyreact_tag(...) as d: child_a(); child_b()` produces the expected DOM in a `shinyreact` example.
- The stack is contextvars-based and safe under async / multiple concurrent contexts (test with concurrent sessions).
- `Tagifiable` instances appended into a parent's children continue to render correctly.

### Stage B — upstream adoption in `py-htmltools`

**Scope.** Port the validated mechanism into `py-htmltools` itself, on `Tag` directly. No Shiny dependency. Documented as a top-level htmltools feature.

**Acceptance (Stage B).**

- `with div(class_="x") as d: h1("title"); p("body")` produces the expected DOM in pure htmltools.
- API and contextvar semantics match the prototype.
- Existing htmltools consumers (Quarto, etc.) are not broken — the feature is opt-in (you only see the behavior if you write `with tag:`).

**Coordination with Shiny.** A follow-up `py-shiny` PR migrates Express's child-collection to use this stack where it cleans up code; otherwise the two coexist (Express's `RecallContextManager` continues to capture *function calls* at the script-body level; the Tag stack captures *Tag construction* inside `with` blocks).

## Migration strategy

- **Stage A (prototype in `shinyreact`):** issues 1 and 3 can be prototyped in parallel; issue 2 depends on issue 1's reference classes. Iterate freely — `shinyreact`'s small surface area and pre-1.0 status make breaking changes cheap. The goal is to discover problems with the design here, not in `py-shiny`.
- **Acceptance gate:** before any Stage B work begins, the team reviews the prototype in `shinyreact` (working examples, snapshot tests, demo of bookmark + update + Express + Core in one app). If the design needs revision, it's revised here.
- **Stage B (upstream adoption):** issues 1 and 3 land independently in their respective upstream repos; issue 2 depends on issue 1's Stage B. All three Stage B changes are designed to be **non-breaking for end users** of `py-shiny` / `py-htmltools`. The only observable runtime difference is `type(ui.input_slider("n", ...))` changes from `Tag` to `UiInputSlider`. A pre-flight grep for `isinstance(_, Tag)` in `py-shiny` itself and known downstream packages happens before issue 1's Stage B lands; if found, the affected sites get an explicit migration note.

## Open questions

These belong in the child issues, not the umbrella, but listing here so they aren't forgotten:

- **Handler registration mechanism.** Explicit module-load `register_input_handler(UiInputDate)` call beside the class definition, vs. a decorator like `@register_input` on the class. Both are explicit; pick one and stick with it for consistency.
- **Bookmark id → class lookup.** Today the session looks up serializers by input id. For the class to own its serializer, the session needs to find the class instance from the id. Two approaches: (a) registration on construction (each `UiInput.__init__` registers `id → self` on the current session if one exists), or (b) walk the rendered Tag tree at session-attach time. Tradeoffs left to issue 1.
- **What `update()` accepts per input.** A single `update(self, **kwargs)` that mirrors today's `update_input_slider(...)` arguments? Or typed per-class `update()` with explicit fields? Answer affects how much typing infrastructure each class carries.
- **Coexistence of Express's `RecallContextManager` and the new Tag stack.** Either layer one on the other or run them side by side with a clear ordering rule (likely: Tag stack wins when both would apply). Decide in issue 3's coordination follow-up.
- **Whether to drop the lowercase function name in a future major.** Out of scope here, but worth noting that once classes are public, the function is technically a candidate for deprecation. Default position: keep both indefinitely — the function is the validating entry point and that's a real role.

## Risks

- **Prototype/upstream drift.** The Stage A reference classes in `shinyreact` and the Stage B `py-shiny` classes risk diverging in subtle ways during the porting step. Mitigation: snapshot tests at the prototype that are reused upstream, and a deliberate pass that walks the prototype file-by-file when porting.
- **Prototype acceptance never happens.** The design might look fine in `shinyreact` but get blocked at the upstream review gate. Mitigation: bring the team in early — share the prototype while it's still small, not after every component has been ported.
- **Hidden coupling on `isinstance(x, Tag)`.** A pre-flight audit in `py-shiny` and downstream packages (e.g., `shinyswatch`, `shinywidgets`, `bslib`-equivalents) is needed before issue 1's Stage B merges. Stage A doesn't trigger this risk because `shinyreact` callers control their own code.
- **Diamond/MRO complexity in `AllowsChildren` inheritance.** `class UiCard(UiLayout, AllowsChildren)` introduces multiple inheritance. Keeping `AllowsChildren` strictly a mixin (no `__init__` of its own that requires cooperation) is a deliberate constraint to keep MRO predictable. Currently only layouts use the mixin; if a future input opts in, the same mixin discipline applies.
- **Documentation churn.** Every `ui.input_*` reference page in the docs site needs to be regenerated to reflect the class at Stage B. Sphinx/Quartodoc pipelines may need adjusting.
- **Issue 3 Stage B affects every htmltools consumer**, not just Shiny. Quarto's Python users, for example. Push back is possible. Mitigation: feature is opt-in semantically (you only see the behavior if you write `with tag:`), and the contextvar stack is safe-by-default outside `with` blocks. Stage A in `shinyreact` lets us demonstrate the feature concretely before pitching it to the htmltools maintainers.

## What this spec does *not* commit to

- Concrete signatures for individual classes — those are component-by-component work in issue 1.
- A specific PR landing order. The umbrella tracks all three; sequencing is decided when issues are scheduled.
- Renaming, removing, or deprecating any existing public symbol.
