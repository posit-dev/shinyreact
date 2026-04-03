# Design: Decompose Hello World Into Registered Components

**Date:** 2026-04-03
**Approach:** B — Fix both examples + update documentation

## Problem

The `1-hello-world` example registers a single monolithic `HelloWorldComponent` that builds its entire UI internally with `React.createElement`. The JSON spec sent from Python is:

```json
{ "root": "hw", "elements": { "hw": { "type": "HelloWorldComponent", "props": {} } } }
```

This defeats the purpose of `@json-render/react`, which is designed for Python to compose a flat tree of registered components via a JSON spec. The whole point of shinyjson is that the server describes the UI structure, not a single JS component.

Additionally, the `hello-shinyjson` example's `Button` component accesses private Shiny internals (`window.Shiny.shinyapp.$inputValues`) instead of using the `useShinyInput` hook.

## Design

### Approach chosen

Fix both examples to demonstrate the intended pattern, update documentation. Keep shinyjson core unchanged (zero components). No Python convenience helpers yet (deferred to future work).

### 1. Hello World Example (`examples/1-hello-world/`)

#### Component library (`hello_world.js`)

Five small, registered components. Each receives `args` (the `ComponentRenderProps` from `@json-render/react`) and uses `args.element.props` for configuration.

| Component | Props | Shiny Hooks | Renders |
|---|---|---|---|
| `Card` | `title` | none | Container div with optional `<h2>` title + `args.children` |
| `Heading` | `text`, `level` (default: 1) | none | `<h1>`–`<h6>` based on level prop |
| `TextInput` | `input_id`, `default_value`, `placeholder`, `label` | `useShinyInput(input_id, default_value)` | Labeled `<input type="text">` |
| `Divider` | none | none | `<hr>` |
| `OutputDisplay` | `output_id`, `label` | `useShinyOutput(output_id, undefined)` | Labeled `<div>` showing server response |

Components are registered via `window.shinyjson.registerComponents(null, { Card, Heading, TextInput, Divider, OutputDisplay })`.

#### App (`app.py`)

Python composes the full UI tree as a flat spec:

```python
@shinyjson.render
def hello():
    return shinyjson.Spec(root="card", elements={
        "card": shinyjson.Element(
            type="Card", props={"title": "Hello Shiny React!"},
            children=["input1", "hr", "display1"],
        ),
        "input1": shinyjson.Element(
            type="TextInput", props={
                "input_id": "txtin",
                "default_value": "Hello, world!",
                "placeholder": "Enter your message here...",
            },
        ),
        "hr": shinyjson.Element(type="Divider", props={}),
        "display1": shinyjson.Element(
            type="OutputDisplay", props={
                "output_id": "txtout",
                "label": "Response from Shiny server:",
            },
        ),
    })

@shinyjson.render
def txtout():
    return input.txtin().upper()
```

The `txtout` render function stays the same — it receives the text input value and returns the uppercased string.

#### Key design decisions

- **Shiny IDs are props, not element keys.** The server needs explicit control over input/output IDs since `@shinyjson.render` and `input.*` reference them by name. Element keys in the spec (e.g., `"input1"`, `"display1"`) are structural identifiers for `@json-render/react`'s flat element map.
- **Components are example-local, not built into shinyjson.** shinyjson remains pure plumbing with zero components. The example is self-contained.

### 2. Hello Shinyjson Example (`examples/hello-shinyjson/`)

#### Button hook migration (`demo_components.js`)

Replace the private Shiny internals access with `useShinyInput`:

**Before:**
```js
function Button(args) {
    var props = args.element.props;
    onClick: function () {
        if (props.input_id && window.Shiny) {
            var prev = window.Shiny.shinyapp.$inputValues[props.input_id] || 0;
            window.Shiny.setInputValue(props.input_id, prev + 1);
        }
    }
}
```

**After:**
```js
function Button(args) {
    var props = args.element.props;
    var result = useShinyInput(props.input_id, 0);
    var count = result[0];
    var setCount = result[1];

    return h("button", {
        onClick: function() { setCount(count + 1); },
        // ... same styling ...
    }, props.label || "Button");
}
```

No changes to `app.py` — it already composes `Card` → `Badge` + `Button` via children IDs correctly.

### 3. Documentation

- **CLAUDE.md:** No changes needed — the "Common patterns" section already documents the `useShinyInput` action button pattern correctly.
- **STATUS.md:** Add bullet under "Recent fixes" for hello world decomposition and Button hook migration.

## JSON Format Validation

The Python `Spec.to_dict()` serialization is **correct** for `@json-render/react`. The library expects:

```json
{
  "root": "element-id",
  "elements": {
    "element-id": {
      "type": "ComponentName",
      "props": {},
      "children": ["child-id-1", "child-id-2"]
    }
  }
}
```

This flat dictionary with children as ID references (not nested objects) is exactly what `Spec`/`Element` produce. No serialization changes needed.

## Future Work (deferred)

See STATUS.md TODOs for:
- Python convenience helpers (Approach C)
- Pretty helper methods for Spec construction
