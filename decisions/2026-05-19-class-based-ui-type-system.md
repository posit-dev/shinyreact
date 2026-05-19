# Class-based UI type system — benefits

**Date:** 2026-05-19
**Status:** Notes — informs Stage B adoption decisions for `py-shiny`
**Related:** `docs/superpowers/specs/2026-05-06-unified-ui-component-class-design.md` (umbrella spec), `docs/superpowers/specs/2026-05-13-shinyui-metadata-consolidation-design.md` (full prototype), `docs/superpowers/specs/2026-05-19-shinyuiclassonly-design.md` (structure-only prototype)

## What "type system" means here

Today's `py-shiny` exposes UI as **function factories**: `ui.card(child, id="m")` returns a `Tag`. The class-based alternative — prototyped in `shinyui` and `shinyuiclassonly` — exposes the same call sites as **classes**: `card(UiLayout, AllowsChildren)` whose `__init__` stores parameters and whose `tagify()` renders to a `Tag` at render time. Every component sits in a small inheritance lattice:

```
UiComponent (ABC, tagify())
├── UiInput            (marker)
├── UiOutput           (marker)
└── UiLayout           (marker)

AllowsChildren         (mixin: children list, __enter__/__exit__)
```

Inputs/outputs are leaves; layouts add `AllowsChildren`. This doc describes the benefits that flow from that change, separates the two independent dimensions the prototypes carve out, and records the costs honestly.

## Two dimensions, not one

This repo ships two sibling prototypes deliberately. They test the two dimensions independently:

| Dimension                       | `shinyuiclassonly`                          | `shinyui`                                     |
|---------------------------------|--------------------------------------------|----------------------------------------------|
| Class hierarchy (structural)    | ✅                                          | ✅                                            |
| Session-bound accessors (ergonomic) | ❌ — server reads `input.<id>()`, updates via `ui.update_*` | ✅ — `slider.value()`, `card.full_screen_value()`, `acc.open_panels()`, `acc.update(open=...)` |

Reviewers can adopt the dimensions on independent timelines. The benefits below are tagged with which prototype demonstrates them.

## Benefits

### 1. Components carry runtime type identity (structural)

Today `ui.card(...)` returns a generic `Tag`. There is no way to ask "is this a card?" — every layout returns the same `Tag` type. Downstream code that needs to recognise components writes string-matching on tag attrs, or `isinstance(x, AccordionPanel)` checks against shiny's private classes.

The class hierarchy makes the check first-class: `isinstance(c, UiLayout)`, `isinstance(c, UiInput)`, `isinstance(panel, accordion_panel)`. `shiny.ui.accordion` already does `isinstance(panel, AccordionPanel)` internally — that pattern is universal in tooling that walks UI trees, and a public class hierarchy makes it a clean API rather than a private contract.

### 2. The factory-vs-`with`-block dichotomy collapses to one symbol (structural)

Today, the same UI tree must be expressed differently depending on Core vs Express:

```python
# Core today
ui.card(ui.div("title"), ui.input_slider("n", "N", 1, 10, 5), id="m")

# Express today (RecallContextManager + Express-specific machinery)
with ui.card(id="m"):
    ui.div("title")
    ui.input_slider("n", "N", 1, 10, 5)
```

The class hierarchy uses `@overload` on a single `__init__` to support both, with one symbol per component:

```python
# shinyuiclassonly — both forms, one class
card(ui.div("title"), input_slider("n", "N", 1, 10, 5), id="m")

with card(id="m"):
    ui.div("title")
    input_slider("n", "N", 1, 10, 5)
```

IDE auto-complete picks the appropriate overload — Express's `with`-block variant lists no positional children, Core's variant lists them — so users see the right signature for the syntax they're typing.

### 3. Co-located metadata per component (structural, leveraged by ergonomics)

Today a date input is spread across at least four files: the UI factory (`ui/_input_date.py`), the input handler registration (`input_handler/_input_handler.py`), the bookmark serializer (`bookmark/_serializers.py`), and the update function (`update_date_input` in another module). Adding a new input requires touching four files; the relationships between them are implicit.

The class hierarchy lets every component own its full lifecycle in one file:

```python
class input_date(UiInput):
    input_handler_name = "shiny.date"
    @staticmethod
    def _input_handler(value, name, session): ...
    bookmark_serializer = DateSerializer
    def __init__(self, id, ...): ...
    def tagify(self) -> Tag: ...
    def value(self) -> date: ...
    def update(self, **kwargs) -> None: ...
```

Adding a new input is one file. The trade-offs are visible in one place. This was the umbrella spec's primary motivation. (`shinyui` demonstrates the full version; `shinyuiclassonly` retains the structural half and shows what's left when the ergonomic half is removed.)

### 4. Static analysis sees real types (structural)

With `ui.card(...) -> Tag`, pyright sees only `Tag` at the call site. There's no way to express "this is a card; it has `full_screen=True`" in the type system. Auto-complete after the dot shows `Tag`'s methods, not the component's.

With `card(...) -> card`, pyright keeps the concrete type. `c.full_screen_value()` (in `shinyui`) is autocompletable. `isinstance(c, AllowsChildren)` lights up only on layouts. Mixed mistakes — `with input_slider(...): ...` — are caught statically because `input_slider` doesn't inherit `AllowsChildren` and so has no `__enter__`/`__exit__`.

### 5. Mixin composition keeps capabilities orthogonal (structural)

`AllowsChildren` is not baked into `UiLayout`. It's an opt-in mixin. A leaf input never accidentally gains a `children` list; a layout that doesn't accept children (rare, but possible) doesn't have to inherit `AllowsChildren`.

Similarly in `shinyui`, `HasInputValue` (input-handler registry + bookmark) is a mixin separate from `Updatable` (server-driven `update()`). A component that can be read but not pushed-to gets `HasInputValue` without `Updatable`. The classes document the capability matrix at declaration time.

The four orthogonal capabilities in `shinyui` — *can carry children* / *exposes a server-readable input* / *supports server-driven update* / *belongs to which role* — are encoded as four mixin slots. Today they're encoded as "look at four other files and hope the names match."

### 6. Server reads keep tagged to their component (ergonomic — `shinyui` only)

In today's Shiny, the connection between a UI factory call and the server's read is by string id only:

```python
# Today
sl = ui.input_slider("n", "N", 1, 10, 5)
# ... later, on the server:
@render.code
def s(): return f"{input.n()}"          # the string "n" must match
```

With `shinyui`, the slider instance carries its own typed read:

```python
n = input_slider("n", "N", 1, 10, 5)
@render.code
def s(): return f"{n.value()}"          # no string-matching; pyright knows .value() exists
```

Rename `n.value()` and the server breaks at type-check time. Misspelled wire ids become a category of bug pyright can catch.

(`shinyuiclassonly` deliberately omits this — its examples use the traditional `input.n()` pattern — to isolate the structural benefit from the ergonomic one.)

### 7. Renderers can auto-place properly-configured outputs (ergonomic — partial in `shinyuiclassonly`)

`shinyui.render_plot` overrides `auto_output_ui()` to emit a `shinyui.output_plot(...)` with matching `click`/`brush` flags. The user writes:

```python
@render_plot(click=True, brush=True)
def plot(): ...
```

— and Express auto-places a properly-configured plot output in the `with` block. Today, the user has to know to write `output_plot("plot", click=True, brush=True)` separately in the UI and `@render.plot(...)` separately in the server, and keep the flags in sync by hand.

`shinyuiclassonly.render_plot` keeps this `auto_output_ui` override (no session needed) and demonstrates a subtle teaching point: `auto_output_ui()` returns the `output_plot` *instance* directly, not `.tagify()`'d. Components stay `Tagifiable` until the framework walks them, which means transformations applied later — wrapping, decorating, conditional rendering — see the structured object, not a frozen `Tag`.

### 8. Closed surface, open extension (structural)

`UiComponent` is an `ABC` with `tagify()` abstract. Downstream packages (`shinyshadcn`, custom dashboards) subclass it directly to plug into the framework's lifecycle. The framework knows how to walk a tree of `UiComponent`s; downstream classes get that walk for free. Today, downstream packages have to imitate the function-factory pattern by hand — a function that returns a `Tag` shaped just right.

### 9. The two prototypes prove the dimensions are separable

The single biggest pedagogical finding of this work is that the structural change and the ergonomic change can be evaluated independently:

- Reading `examples/14` against `examples/16` shows what disappears when the session-bound accessors are removed. The class hierarchy stays; the `with`-block ergonomics stay; only the `.value()` / `.update()` / `.click_value()` calls go.
- Reading `examples/16` against today's `ui.card()` code shows what the class hierarchy alone buys you, *before* the ergonomic layer.

A team that wants only the structural change can adopt `shinyuiclassonly`'s shape upstream. A team that wants the full version can adopt `shinyui`'s. The decision is two-axis, not one.

## Costs

This isn't free. The honest list:

- **Backwards compatibility.** Existing user code that depends on `ui.card(...)` returning a `Tag` keeps working only because the class instance is `Tagifiable` — so `tag.children.append(card(...))` and `str(some_tag_list)` both still produce the same HTML. But code that does `isinstance(x, Tag)` on a UI tree will see `False` for the class instances and need either a type-alias shim or a deprecation path. py-shiny would need to decide whether to keep returning `Tag` from the public factories or to flip the return type.
- **`@overload` doubles the surface area per class.** Two signatures (Express + Core) per layout class. IDE help becomes denser. The implementation `__init__` has to accept the union of both; we use `*args` + keyword-only kwargs to satisfy both.
- **MRO discipline.** `AllowsChildren.__init__` calls `super().__init__(**kwargs)`. Concrete classes have to call `super().__init__(*args)` so children flow through. Subtle but enforced — pyright in strict mode would catch most misses, and the existing test suite catches the rest.
- **Cooperative `__init_subclass__`.** `shinyui`'s `HasInputValue.__init_subclass__` auto-registers input handlers at class-definition time. Reading the class no longer tells you what happens — there's now machinery the class header triggers. (`shinyuiclassonly` deliberately omits this, which is the single biggest reason the package is so much smaller.)
- **Per-session instance registry.** `shinyui` attaches `_shinyui_instances` to each Shiny `Session` to support `lookup_component(session, id)`. This is private-attribute touching today; Stage B would need a public `py-shiny` hook. `shinyuiclassonly` again omits this entirely.
- **Class explosion in downstream packages.** Every downstream UI package gains a parallel set of class names — `shinyshadcn.Button`, `shinyshadcn.Card`, … — instead of just functions. Mostly mechanical, but it's more public surface to maintain.
- **Snake_case class names.** The classes are named `card`, `input_slider`, `accordion_panel` — call-site identical to today. Ruff's `N801` ("class names should use CapWords") needs a per-package ignore. The trade-off is small (one ruff line) and the win is large (no parallel `Card` vs. `card` factory naming).

## What `shinyuiclassonly` specifically proves

The structure-only prototype settles one question that wasn't obvious from the umbrella spec: *does the class hierarchy carry its weight without the session-bound accessors?* The answer is **yes**, and the case is:

1. The two examples (16-core and 17-express) read clearly without any walrus-binding gymnastics, because the server can just call `input.n()` like today.
2. `make py-check` is green across 91 tests with no session-related plumbing whatsoever.
3. The package source totals about 600 lines including docstrings — the entire "class hierarchy" idea fits in something small enough to read in one sitting.
4. Components are pure `Tagifiable` objects; no per-session state means no lifecycle complexity. A `card(id="m")` instance can be constructed at module top level once and reused across sessions — a property that's harder to claim about `shinyui` because of its `_session` capture and per-session id registry.

Put another way: the class hierarchy isn't a load-bearing prerequisite for the accessor layer; it's a stand-alone improvement that the accessor layer can later build on.

## Next steps for upstream adoption

Three independently-shippable child issues, in dependency order:

1. **Tag as context manager** (`py-htmltools`). Independent of the rest. Lets `with ui.div(): ...` work outside Express. Prototyped via `CtxTag` in both packages.
2. **Class-per-component, structure only** (`py-shiny`). The `shinyuiclassonly` shape: `UiComponent` / role markers / `AllowsChildren` / one class per existing factory. Public factories keep returning the class instance (now `Tagifiable`, still backwards-compatible at the HTML output level).
3. **Session-bound accessors and `update()` on the instance** (`py-shiny`). The `shinyui` shape: add `HasInputValue`, `Updatable`, `reactive_calc_method`, per-session id registry, `.value()` / `.update()` methods on concrete classes. Depends on (2) but doesn't have to ship together.

A team that lands only (1) and (2) already gets the structural benefits listed above (1–5, 8) without committing to the lifecycle complexity of (3). A team that also lands (3) gets benefits 6 and 7 on top. That decoupling is the most actionable thing this repo has produced.
