# `shinyui` — metadata consolidation prototype (Stage A of umbrella #68 / issue #69)

**Date:** 2026-05-13
**Status:** Design
**Scope:** Stage A only — prototype the class hierarchy in a new sibling Python package, `shinyui`, inside this repo. Stage B porting to `py-shiny` is explicitly out of scope.
**Tracks:** GitHub issue [#69](https://github.com/posit-dev/shinyreact/issues/69) under umbrella [#68](https://github.com/posit-dev/shinyreact/issues/68).
**Reference design:** [`2026-05-06-unified-ui-component-class-design.md`](./2026-05-06-unified-ui-component-class-design.md) (umbrella). This spec refines the issue-69 portion and supersedes parts of the umbrella where they diverge (notably the `UiInput`/`UiLayout` straddler model and `update()` argument shape).

## Summary

Build a new Python package `shinyui` at `pkg-py/src/shinyui/` that prototypes a class-per-component UI hierarchy. Each class owns its own metadata (input handler, bookmark serializer, HTML deps, `update()` method, server-side read accessors). The package depends only on `shiny` and `htmltools` — *not* on `shinyreact` — so the eventual Stage B port into `py-shiny` is a near-mechanical copy.

The prototype ships at least seven concrete classes covering every archetype: simple input, structured input, plain output, output-with-read-only-signals (plot), layout-with-children, layout-with-state (card, accordion), and layout-as-child-of-layout. The implementation also adds `input_action_button` to exercise the `__init_subclass__` handler-registration demo (see below).

Three open questions from the umbrella are resolved in this spec:

- **Handler registration:** `cls._register_input_handler()` is a classmethod on `HasInputValue`; it is auto-fired by `HasInputValue.__init_subclass__` whenever any subclass is defined. Subclasses that leave `input_handler_name = ""` (the default) are a no-op — slider, select, card, accordion, and the plot/code outputs all take that path. `input_action_button` is the one class in the prototype that opts into a custom wire-side coercion handler, registered under `"shinyui.action"`.
- **Bookmark id → instance lookup:** register-on-construction; `__init__` queries `get_current_session()` and registers `(id, self)` on the session if one is in scope. No-op if not (module-level UI keeps working, just without class-owned serializers).
- **`update()` signature:** typed per-class keyword arguments. No `session=` kwarg — session is captured at `__init__` and resolved at call time via a shared `_require_session()` helper.

A fourth refinement that emerged during design:

- The umbrella's `UiInput`/`UiLayout`/`UiOutput` straddler pattern (e.g. `accordion(UiInput, AllowsChildren)`) is replaced. "Has an input value" and "is updatable" become orthogonal mixins (`HasInputValue`, `Updatable`); the three role classes stay as semantic markers. This avoids the awkwardness of calling a card or an accordion "an input."

## Motivation (delta from umbrella)

The umbrella spec answers *why* this work matters and *what* the hierarchy looks like. This spec answers *where it lives*, *which seven classes to build*, *how the lifecycle resolves the three open questions*, and *what tests pin the design.*

Three concrete pressures shaped the divergences below:

- **Layouts can have input values.** Accordion's open-panel set, card's full-screen toggle, sidebar's open/closed state, navset's active tab — all are layouts whose primary user-facing purpose is structure, but which expose server-readable state. The umbrella's `accordion(UiInput, AllowsChildren)` straddler doesn't generalize gracefully to `card` ("a card is an input?"). Factoring `HasInputValue` out as a mixin removes the awkwardness and reads honestly.
- **Outputs can have read-only multi-signals.** A plot exposes `<id>_click`, `<id>_brush`, `<id>_hover`, `<id>_dblclick`. None are updatable from the server. Forcing these through `HasInputValue` (multi-id generalization) inflates a single-id abstraction for one rare use case; making them a separate mechanism keeps the common case clean.
- **Server-side read accessors are a real ergonomic win.** Shiny's `@render.data_frame` already exposes `df.cell_selection()`, `df.sort()`, etc. as reactive methods on the renderer instance. The class-per-component design makes the same idiom available across the board: `slider.value()`, `card.full_screen_value()`, `accordion.open_panels()`, `plot.click_value()`.

## Goals

- One Python file per component class containing its full lifecycle (markup, handler, serializer, deps, update, read accessors).
- A single shared `_require_session()` helper on `UiComponent` powering update, `_read_input()`, and plot's `_read_signal()`.
- Snapshot equivalence between `shinyui.*` `tagify()` output and the corresponding `shiny.ui.*` output, so Stage B porting is provably markup-neutral.
- Working end-to-end example app exercising every archetype, with bookmark round-trip and at least one `.update()` call from the server.
- A test suite that pins MRO, registration, bookmark resolution, update resolution, and read-accessor behavior independently — so a regression at any one layer surfaces immediately.

## Non-goals

- Stage B port into `py-shiny` (separate issue when this prototype is accepted).
- Tag-as-context-manager / parent-tag stack (umbrella sub-issue 3; `AllowsChildren.__enter__` returns `self` and the auto-collect-bare-tags behavior is deferred).
- Core/Express overload signature unification (umbrella sub-issue 2).
- Adding shinyui imports to `pkg-py/src/shinyreact/`. The two packages are independent.
- Replacing existing shinyreact examples or APIs.

## Package layout

```
pkg-py/
  src/
    shinyreact/         # existing
    shinyui/            # new
      __init__.py
      _base.py          # UiComponent, AllowsChildren
      _mixins.py        # HasInputValue, Updatable
      _reactive.py      # local reactive_calc_method (~15 lines, comment cites shiny/render/_data_frame_utils/_reactive_method.py)
      _input_slider.py
      _input_select.py
      _output_code.py
      _output_plot.py
      _card.py
      _accordion.py
  tests/
    shinyui/
      test_hierarchy.py
      test_tagify_snapshots.py
      test_input_handler_registration.py
      test_bookmark_roundtrip.py
      test_update_resolution.py
      test_read_accessors.py
      test_allows_children.py
```

The root `pyproject.toml` is extended:

```toml
[tool.hatch.build.targets.wheel]
packages = ["pkg-py/src/shinyreact", "pkg-py/src/shinyui"]

[tool.pyright]
include = ["pkg-py/src/shinyreact", "pkg-py/src/shinyui"]
```

`make py-check` automatically covers `shinyui` (pytest collects under `pkg-py/tests/` by default; pyright scans both packages).

Deps: `shiny + htmltools` (already in the project's runtime deps). No new dependency.

## Class hierarchy

```
UiComponent (ABC)              # tagify() abstract; __enter__ raises; _session; _require_session(); _read_input()
  ├── UiInput(UiComponent, HasInputValue)        # "primarily an input control"
  ├── UiOutput(UiComponent)                      # "primarily a server-rendered output"; has id
  └── UiLayout(UiComponent)                      # "primarily a container"; no id by itself

HasInputValue (mixin)          # id, bookmark_serializer (class default + per-instance override), session-time id→instance registration
Updatable (ABC mixin)          # update(**kwargs) abstract; subclasses give typed kwargs
AllowsChildren (mixin)         # children, append(), __enter__ returns self, __exit__
```

**Rules:**

- `UiComponent.__enter__` raises `TypeError`. `AllowsChildren.__enter__` overrides to return `self`.
- A class can be used in `with` iff `AllowsChildren` is in its bases.
- A class has a server-readable id iff `HasInputValue` is in its bases, OR it is a `UiOutput`. (`UiOutput` carries its own `id` independent of `HasInputValue` — outputs need an id for rendering but don't need bookmark/serializer machinery.)
- A class supports `.update()` iff `Updatable` is in its bases.
- Cooperative `__init__`: every mixin calls `super().__init__(**kw)` first, then does its own work. This guarantees `UiComponent.__init__` (which captures `self._session`) has already run before any mixin reads it.

### Concrete reference set

| Class | Bases | Has input value? | Updatable? | Read accessors |
|---|---|---|---|---|
| `input_slider` | `UiInput, Updatable` | ✓ | ✓ | `value() -> float` |
| `input_select` | `UiInput, Updatable` | ✓ | ✓ | `value() -> str \| tuple[str, ...]` |
| `output_code` | `UiOutput` | — | — | — |
| `output_plot` | `UiOutput` | ✓ (derived ids; not `HasInputValue`) | — | `click_value()`, `dblclick_value()`, `hover_value()`, `brush_value()` |
| `card` | `UiLayout, AllowsChildren, HasInputValue, Updatable` | ✓ — `full_screen` (empty suffix; `input.<id>()` is the boolean) | ✓ | `full_screen_value() -> bool` |
| `accordion` | `UiLayout, AllowsChildren, HasInputValue, Updatable` | ✓ — open panel set | ✓ | `open_panels() -> tuple[str, ...]` |
| `accordion_panel` | `UiLayout, AllowsChildren` | — | — | — |

Concrete classes use snake_case names (matching `shiny.render.data_frame` convention). The class name IS the call site — no separate factory function. Public exports from `shinyui`.

### Why this departs from the umbrella

The umbrella spec models `accordion` as `UiInput, AllowsChildren` (a "straddler"). That works for accordion in isolation but doesn't generalize to `card`: a card whose full-screen state is exposed as an input wouldn't naturally be called "an input." Once we admit that *any* layout can expose state, the cleanest factoring is to make state-bearing a mixin orthogonal to the role split. The role categories (`UiInput`/`UiOutput`/`UiLayout`) become semantic markers; the mixins (`HasInputValue`/`Updatable`/`AllowsChildren`) describe capabilities.

This refactor doesn't change the umbrella's other commitments: HTML deps still live as ClassVar, `tagify()` is still pure, the input handler registry is unchanged, and the umbrella's "you can `with X(...)` iff `X` declares `AllowsChildren`" rule still holds.

## Lifecycle decisions

### Session capture — single source of truth on `UiComponent`

```python
class UiComponent(ABC):
    html_dependencies: ClassVar[tuple[HTMLDependency, ...]] = ()

    def __init__(self, **kwargs):
        self._session: Session | None = get_current_session()  # may be None at module load
        super().__init__(**kwargs)

    def _require_session(self, *, for_op: str) -> Session:
        sess = self._session or get_current_session()
        if sess is None:
            raise RuntimeError(
                f"{type(self).__name__}.{for_op}() requires an active session "
                f"(instance constructed outside any session, and none is active now)"
            )
        return sess

    def _read_input(self, suffix: str = "") -> Any:
        sess = self._require_session(for_op="_read_input")
        return sess.input[f"{self.id}{suffix}"]()

    @abstractmethod
    def tagify(self) -> Tag: ...

    def __enter__(self) -> Self:
        raise TypeError(
            f"{type(self).__name__} does not accept children; "
            f"only components declaring `AllowsChildren` may be used as `with` blocks."
        )
    def __exit__(self, *exc): ...
```

`_read_input` lives on `UiComponent` so plot, slider, card, accordion, etc. all share one implementation. The only precondition is that `self.id` exists — guaranteed by `UiOutput` or `HasInputValue`.

### Construction always succeeds

`__init__` never raises for absence-of-session. Module-level UI declarations (`app_ui = page_react(...)`) continue to work, but bookmark serializers won't be class-owned for those instances (no session at construction → no id→instance registration → bookmark falls through to Shiny's default path). Apps that need bookmark of class-owned serializers must use the function-form `def app_ui(request): ...` so a session is in scope when instances are constructed.

### Session-requiring methods throw at call time

`update()`, `_read_input()`, `_read_signal()` all funnel through `_require_session(for_op=...)`. If no session is reachable (neither captured at init nor active now), a `RuntimeError` is raised with the class name and method name in the message.

### Input handler registration — explicit module-level call

```python
class HasInputValue:
    input_handler_name: ClassVar[str] = ""
    _input_handler: ClassVar[Callable[..., Any] | None] = None
    bookmark_serializer: ClassVar[BookmarkSerializer | None] = None

    @classmethod
    def _register_input_handler(cls) -> None:
        """Idempotent. Call once at module load if this class declares a handler."""
        if cls.input_handler_name and cls._input_handler is not None:
            register_input_handler(cls.input_handler_name, cls._input_handler)

    def __init__(self, *, id: str, **kwargs):
        self.id = id
        super().__init__(**kwargs)  # UiComponent sets self._session
        if self._session is not None:
            _register_instance_on_session(self._session, id, self)
```

Subclasses declare both attributes and call `_register_input_handler()` at module level:

```python
class input_date(UiInput):  # noqa: N801
    input_handler_name = "shiny.date"

    @staticmethod
    def _input_handler(value, name, session):
        return parse_iso_date(value)


input_date._register_input_handler()
```

Most simple inputs (slider, select, code, card, accordion, plot, etc.) don't override `_input_handler` and don't call `_register_input_handler()` — the default `None` means "Shiny's existing wire layer passes the value through as-is."

Why not `__init_subclass__`: import-order coupling, abstract-intermediate footgun, test-inheritance side effects, and "where is this registered?" greppability. All five concerns documented in conversation; sticking with explicit-call discipline matches `py-shiny`'s existing style and makes Stage B porting trivially mechanical.

### Bookmark id → instance lookup — register on construction

When `HasInputValue.__init__` finds an active session, it registers `(id, self)` on a session-attached map (`session._shinyui_instances: dict[str, HasInputValue]` or equivalent attached via `setattr` on first use, since we don't own `Session`). On bookmark save, the bookmark machinery walks this map for class-owned serializers; on restore, it looks up by id and applies the class's `deserialize` before Shiny's default flow. For ids not in the map, the existing Shiny path applies.

Per-instance serializer override: `HasInputValue` reads `getattr(self, "_bookmark_serializer", None) or type(self).bookmark_serializer`. Users can pass `bookmark_serializer=` to the factory to override per-instance without subclassing.

### `update()` — typed per-class, no session arg

```python
class Updatable(ABC):
    @abstractmethod
    def update(self, **kwargs) -> None: ...


class input_slider(UiInput, Updatable):  # noqa: N801
    def update(
        self, *,
        value: float | tuple[float, float] = MISSING,
        min: float = MISSING,
        max: float = MISSING,
        step: float = MISSING,
        label: str = MISSING,
    ) -> None:
        sess = self._require_session(for_op="update")
        # Mirror shiny.ui.update_slider's send_input_message payload:
        sess.send_input_message(self.id, _build_slider_update_payload(...))
```

No `session=` kwarg. Session is captured at `__init__` (in `UiComponent`) and resolved at call time via `_require_session()`. If the instance was constructed outside any session, `_require_session()` falls back to `get_current_session()`; if both are None, it raises.

Each class with `Updatable` defines its own typed signature. Mechanical mirror of today's `update_input_*` modules — same fields, same defaults, same payload shape. Pyright catches drift between `__init__` and `update()` arg sets (where they overlap).

### Server-side read accessors

The data_frame renderer pattern: instance methods wrapped in `@reactive_calc_method`, each calling `_read_input()` (single-signal) or `_read_signal()` (multi-signal) under the hood.

For `HasInputValue` (single-id):

```python
class input_slider(UiInput, Updatable):  # noqa: N801
    @reactive_calc_method
    def value(self) -> float:
        return self._read_input()


class card(UiLayout, AllowsChildren, HasInputValue, Updatable):  # noqa: N801
    @reactive_calc_method
    def full_screen_value(self) -> bool:
        return bool(self._read_input())


class accordion(UiLayout, AllowsChildren, HasInputValue, Updatable):  # noqa: N801
    @reactive_calc_method
    def open_panels(self) -> tuple[str, ...]:
        return tuple(self._read_input() or ())
```

For `output_plot` (multi-signal, not `HasInputValue`):

```python
class output_plot(UiOutput):  # noqa: N801
    def __init__(
        self, id: str, *,
        click: bool = False, dblclick: bool = False,
        hover: bool = False, brush: bool = False,
    ):
        self.id = id
        self._click = click
        self._dblclick = dblclick
        self._hover = hover
        self._brush = brush
        super().__init__()

    @reactive_calc_method
    def click_value(self)    -> dict | None: return self._read_input("_click")
    @reactive_calc_method
    def dblclick_value(self) -> dict | None: return self._read_input("_dblclick")
    @reactive_calc_method
    def hover_value(self)    -> dict | None: return self._read_input("_hover")
    @reactive_calc_method
    def brush_value(self)    -> dict | None: return self._read_input("_brush")

    def tagify(self) -> Tag: ...  # markup copied from shiny.ui.output_plot
```

Plot deliberately does *not* register input handlers for its derived ids. Shiny's `Inputs.__getitem__` auto-creates a read-only `Value[Any]` on first access; the browser pushes JSON to those ids over the wire; the accessors read them. No new abstraction needed in the common path.

### `_reactive_calc_method` helper

Implemented locally in `shinyui/_reactive.py` (~15 lines): `@reactive.calc`-wrapped per-instance cache via `WeakKeyDictionary`. Comment cites `shiny/render/_data_frame_utils/_reactive_method.py` as the inspiration. Stage B can decide whether to extract the helper to a public Shiny utility.

### `tagify()` is pure

No `get_current_session()`, no registration side effects, no mutation of class state. Safe to call multiple times for the same instance. The renderer (Shiny, htmltools) is allowed to call `tagify()` more than once per render pass.

HTML deps come from `cls.html_dependencies`. `tagify()` returns a `Tag` with deps attached via the standard htmltools `Tag` mechanism.

### `AllowsChildren` — no parent-tag stack here

```python
class AllowsChildren:
    def __init__(self, *children, **kwargs):
        self.children: list[TagChild] = list(children)
        super().__init__(**kwargs)

    def append(self, child: TagChild) -> Self:
        self.children.append(child)
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc): ...
```

`with card(id="c") as c: c.append(child)` works. `with card(id="c"): h1("title")` does *not* auto-collect `h1` — that's umbrella sub-issue 3 (Tag-as-context-manager), explicitly out of scope here.

## Example app — `examples/app-py/14-unified-ui-prototype/`

A single example exercises every reference class in one page. The `app_ui` is a function so a session is in scope at construction, demonstrating bookmark of class-owned serializers.

```python
import shinyui as su
from shiny import App, reactive
import shinyreact

def app_ui(request):
    return shinyreact.page_react(
        # Layout-as-child-of-layout + layout-with-state + simple input + output:
        su.card(
            su.input_slider("n", "N", 1, 100, 50),
            su.input_select("col", "Column", {"a": "A", "b": "B"}),
            su.output_code("summary"),
            su.output_plot("plot", click=True, brush=True),
            su.accordion(
                su.accordion_panel("Settings", "..."),
                su.accordion_panel("Diagnostics", "..."),
                id="acc",
                open="Settings",
            ),
            id="main_card",
            full_screen=False,
        ),
    )

def server(input, output, session):
    plot     = ...  # retrieved from session by id or by referencing closures
    card     = ...
    accordion = ...

    @reactive.effect
    def _():
        if (c := plot.click_value()) is not None:
            print(f"click @ {c['x']},{c['y']}")

    @reactive.effect
    def _():
        if input.n() > 90:
            card.update(full_screen=True)
            accordion.update(open=("Diagnostics",))

    @su.render_code  # or whichever render shape we expose for output_code
    def summary(): ...
```

A README in the example folder walks through each archetype, what it demonstrates, and how to verify the bookmark round-trip (URL state in `?_inputs_=...`).

(Implementation detail: how the server captures `plot` / `card` / `accordion` instances — whether via factory closures, lookup-by-id on a session-attached registry, or another path — is settled in the implementation plan, not this design.)

## Test suite

Each test file targets one layer. Tests use a controllable session via Shiny's session helpers (`session_context` or equivalent) so `get_current_session()` returns a mock.

| Test file | What it pins |
|---|---|
| `test_hierarchy.py` | MRO of every concrete class; `isinstance(slider, UiInput)`, `isinstance(card, AllowsChildren)`, etc.; `with input_slider(...):` raises `TypeError` with the right message; `with output_code(...):` likewise; `with card(...):` does not. |
| `test_tagify_snapshots.py` | `tagify()` output for each class compared to the equivalent `shiny.ui.*(...)` `Tag` — Tag equality + HTML-dep set equality. Catches drift from upstream markup. |
| `test_input_handler_registration.py` | After importing `shinyui`, the handler registry contains the expected `input_handler_name` → callable mappings (e.g. for `accordion`); classes without `_input_handler` don't register anything. |
| `test_bookmark_roundtrip.py` | Within a session, construct an input, serialize via the class-owned serializer (or per-instance override), restore in a fresh session, assert value parity. |
| `test_update_resolution.py` | `update()` outside a session raises `RuntimeError` with class name + method name; with init-captured session it uses that session; with no init session but a current session it uses the current; `update()` accepts no `session=` kwarg (type-checked via pyright fixture). |
| `test_read_accessors.py` | `slider.value()`, `card.full_screen_value()`, `accordion.open_panels()`, `plot.click_value()` each return the value from the appropriate `session.input[derived_id]`; called outside a session, each raises. |
| `test_allows_children.py` | `card.append(child)` mutates `card.children`; `with card(id=...) as c: c.append(x)` collects `x` correctly; appending to a non-`AllowsChildren` raises `AttributeError`. |

Snapshot test infrastructure reuses the existing `make py-update-snaps` flow.

## Acceptance criteria (Stage A)

Mirroring the issue's checklist:

- [ ] `pkg-py/src/shinyui/` exists with `UiComponent`, `UiInput`, `UiOutput`, `UiLayout`, `HasInputValue`, `Updatable`, `AllowsChildren` and the seven concrete classes.
- [ ] Each class has its factory function exported alongside the class.
- [ ] `examples/app-py/14-unified-ui-prototype/` runs end-to-end with bookmark round-trip and at least one `.update()` from the server.
- [ ] All seven test files exist and pass; `make py-check` is green.
- [ ] `tagify()` snapshots match `shiny.ui.*` markup for every concrete class.
- [ ] `with input_slider(...):` (and any non-`AllowsChildren` instance) raises with a clear message naming the class.
- [ ] No new top-level dependency added to `pyproject.toml`.

## Open questions deferred

- **Sub-issue 2 (Core/Express overload signatures)** — out of scope here. Will be designed in a follow-up brainstorm; depends on this prototype landing.
- **Sub-issue 3 (Tag-as-context-manager / parent-tag stack)** — out of scope here. `AllowsChildren.__enter__` returns `self` and `with card(): h1("x")` does *not* auto-collect.
- **How `server()` captures component instances** — closure capture, lookup-by-id from a session-attached registry, or another path. Settled in the implementation plan, not this design.
- **`output_code` rendering** — whether `shinyui` ships its own `@render_code` decorator or relies on `shiny.render.code`. Settled in the implementation plan.

## Risks

- **MRO discipline.** `card(UiLayout, AllowsChildren, HasInputValue, Updatable)` is four-base inheritance. Each mixin must `super().__init__(**kw)` first, then do its own work. Documented in code comments; pinned by `test_hierarchy.py`. If a mixin omits `super()`, errors surface immediately because `self._session` won't be set when `HasInputValue` reads it.
- **Snapshot drift.** Upstream `shiny.ui` markup can change between releases. Snapshot test runs against the installed `shiny`, so changes are caught on dependency bumps. Mitigation: pin `shiny>=1.2.0` (already done) and regenerate snapshots when bumping.
- **Bookmark coupling to private session state.** Attaching `_shinyui_instances` to `Session` via `setattr` is a private-attribute pattern. Acceptable for a prototype; Stage B can negotiate a public hook in `py-shiny`.
- **`@reactive_calc_method` local fork.** Drift from `shiny.render._data_frame_utils._reactive_method` is possible. Mitigation: 15-line implementation, comment pointing at the source, easy to compare during Stage B.
- **Express usage.** Express's `RecallContextManager` is not integrated. Using `shinyui` factories inside Express may or may not collect children correctly — this prototype does not promise Express ergonomics (sub-issue 2 scope).

## What this spec does not commit to

- The exact wire-payload shape of `update()` per class (mirrors `shiny.ui.update_*` — same fields, same defaults, same encoding — but exact field-by-field specifications are an implementation concern).
- The Stage B port plan.
- A migration strategy for existing shinyreact examples (none of them use `shinyui`; they keep working unchanged).
