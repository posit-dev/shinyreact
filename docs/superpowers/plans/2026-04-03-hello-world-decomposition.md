# Hello World Decomposition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompose the monolithic hello world example into small registered components composed from Python, and migrate the hello-shinyjson Button to use the `useShinyInput` hook.

**Architecture:** Rewrite `examples/1-hello-world/hello_world.js` to register five small components (Card, Heading, TextInput, Divider, OutputDisplay). Rewrite `examples/1-hello-world/app.py` to compose the full UI tree using the `Node`-based approach and Python helper functions, rather than composing `Spec` directly. Migrate `examples/hello-shinyjson/demo_components.js` Button from private Shiny internals to `useShinyInput`. Update STATUS.md.

**Tech Stack:** Plain JavaScript (no JSX/bundler), Python/Shiny, `@json-render/react` component registry

**Spec:** `docs/superpowers/specs/2026-04-03-hello-world-decomposition-design.md`

> **Note (2026-04-10):** The referenced design spec captures the original plan using `Spec` directly. The implementation evolved to use `shinyjson.Node` (nested tree that auto-flattens to `Spec`) with Python helper functions. Where the spec differs from the code, the implemented `Node`-based approach is authoritative.

---

### Task 1: Rewrite hello_world.js with five registered components

**Files:**
- Modify: `examples/1-hello-world/hello_world.js`

- [ ] **Step 1: Replace the entire file contents**

Replace `examples/1-hello-world/hello_world.js` with:

```js
// hello_world.js — Registers small, composable components for the
// 1-hello-world example. Each component receives `args` (ComponentRenderProps
// from @json-render/react) and reads configuration from `args.element.props`.
(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useShinyInput = window.shinyjson.useShinyInput;
  var useShinyOutput = window.shinyjson.useShinyOutput;

  // Card: styled container with optional title and children
  function Card(args) {
    var props = args.element.props;
    return h(
      "div",
      { className: "card" },
      props.title ? h("h1", null, props.title) : null,
      args.children
    );
  }

  // Heading: renders h1–h6 based on level prop (default: 1)
  function Heading(args) {
    var props = args.element.props;
    var tag = "h" + (props.level || 1);
    return h(tag, null, props.text || "");
  }

  // TextInput: labeled text input wired to Shiny via useShinyInput
  function TextInput(args) {
    var props = args.element.props;
    var result = useShinyInput(props.input_id, props.default_value || "");
    var value = result[0];
    var setValue = result[1];

    return h(
      "div",
      { className: "input-group" },
      props.label ? h("label", null, props.label) : null,
      h("input", {
        type: "text",
        value: value,
        onChange: function (e) { setValue(e.target.value); },
        placeholder: props.placeholder || "",
      })
    );
  }

  // Divider: horizontal rule
  function Divider() {
    return h("hr");
  }

  // OutputDisplay: labeled display area wired to Shiny via useShinyOutput
  function OutputDisplay(args) {
    var props = args.element.props;
    var result = useShinyOutput(props.output_id, undefined);
    var value = result[0];

    return h(
      "div",
      { className: "output-section" },
      props.label
        ? h("label", { className: "output-label" }, props.label)
        : null,
      h("div", { className: "output-content" }, value)
    );
  }

  window.shinyjson.registerComponents(null, {
    Card: Card,
    Heading: Heading,
    TextInput: TextInput,
    Divider: Divider,
    OutputDisplay: OutputDisplay,
  });
})();
```

- [ ] **Step 2: Verify the file was written correctly**

Run: `head -5 examples/1-hello-world/hello_world.js`

Expected output starts with:
```
// hello_world.js — Registers small, composable components for the
```

- [ ] **Step 3: Commit**

```bash
git add examples/1-hello-world/hello_world.js
git commit -m "refactor(1-hello-world): decompose into five registered components

Replace monolithic HelloWorldComponent with Card, Heading, TextInput,
Divider, and OutputDisplay — each receiving config via args.element.props."
```

---

### Task 2: Rewrite app.py to compose the full spec tree

**Files:**
- Modify: `examples/1-hello-world/app.py`

- [ ] **Step 1: Replace the entire file contents**

Replace `examples/1-hello-world/app.py` with:

```python
from pathlib import Path

import shinyjson
from htmltools import HTMLDependency
from shiny import App, Inputs, Outputs, Session

_hello_dep = HTMLDependency(
    name="hello-world",
    version="0.1.0",
    source={"subdir": str(Path(__file__).parent)},
    script={"src": "hello_world.js", "defer": ""},
    stylesheet={"href": "styles.css"},
)

app_ui = shinyjson.ui("hello", extra_deps=[_hello_dep])


def server(input: Inputs, output: Outputs, session: Session):
    @shinyjson.render
    def hello():
        return shinyjson.Spec(
            root="card",
            elements={
                "card": shinyjson.Element(
                    type="Card",
                    props={"title": "Hello Shiny React!"},
                    children=["input1", "hr", "display1"],
                ),
                "input1": shinyjson.Element(
                    type="TextInput",
                    props={
                        "input_id": "txtin",
                        "default_value": "Hello, world!",
                        "placeholder": "Enter your message here...",
                        "label": "Type something to send to Shiny server:",
                    },
                ),
                "hr": shinyjson.Element(type="Divider", props={}),
                "display1": shinyjson.Element(
                    type="OutputDisplay",
                    props={
                        "output_id": "txtout",
                        "label": "Response from Shiny server:",
                    },
                ),
            },
        )

    @shinyjson.render
    def txtout():
        return input.txtin().upper()


app = App(app_ui, server)
```

- [ ] **Step 2: Run Python format check on the file**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/quito && uv run ruff check examples/1-hello-world/app.py && uv run ruff format --check examples/1-hello-world/app.py`

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add examples/1-hello-world/app.py
git commit -m "refactor(1-hello-world): compose UI tree from Python via Spec

Python now describes the full component tree (Card > TextInput + Divider +
OutputDisplay) instead of delegating to a single HelloWorldComponent."
```

---

### Task 3: Migrate hello-shinyjson Button to useShinyInput

**Files:**
- Modify: `examples/hello-shinyjson/demo_components.js`

- [ ] **Step 1: Replace the Button function**

In `examples/hello-shinyjson/demo_components.js`, make two changes:

**Change 1:** Add `useShinyInput` to the variable declarations at the top of the IIFE (after line 6):

Replace:
```js
  var React = window.shinyjson.React;
  var h = React.createElement;
```

With:
```js
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useShinyInput = window.shinyjson.useShinyInput;
```

**Change 2:** Replace the entire Button function (lines 60–88):

Replace:
```js
  // Button: styled button that sends clicks to Shiny via Shiny.setInputValue
  function Button(args) {
    var props = args.element.props;
    return h(
      "button",
      {
        style: {
          padding: "8px 16px",
          borderRadius: "6px",
          border: "none",
          backgroundColor: props.color || "#4a90d9",
          color: "#fff",
          fontSize: "0.9rem",
          fontWeight: "500",
          cursor: "pointer",
          marginRight: "6px",
        },
        // TODO: Migrate to useShinyInput hook instead of accessing private
        // Shiny internals ($inputValues). This pattern is fragile and may break
        // with future Shiny updates.
        onClick: function () {
          if (props.input_id && window.Shiny) {
            var prev = window.Shiny.shinyapp.$inputValues[props.input_id] || 0;
            window.Shiny.setInputValue(props.input_id, prev + 1);
          }
        },
      },
      props.label || "Button"
    );
  }
```

With:
```js
  // Button: styled button that sends clicks to Shiny via useShinyInput
  function Button(args) {
    var props = args.element.props;
    var result = useShinyInput(props.input_id, 0);
    var count = result[0];
    var setCount = result[1];

    return h(
      "button",
      {
        style: {
          padding: "8px 16px",
          borderRadius: "6px",
          border: "none",
          backgroundColor: props.color || "#4a90d9",
          color: "#fff",
          fontSize: "0.9rem",
          fontWeight: "500",
          cursor: "pointer",
          marginRight: "6px",
        },
        onClick: function () {
          setCount(count + 1);
        },
      },
      props.label || "Button"
    );
  }
```

- [ ] **Step 2: Verify the file looks correct**

Run: `grep -n "useShinyInput\|setInputValue\|\$inputValues" examples/hello-shinyjson/demo_components.js`

Expected: Only `useShinyInput` references, no `setInputValue` or `$inputValues`.

- [ ] **Step 3: Commit**

```bash
git add examples/hello-shinyjson/demo_components.js
git commit -m "fix(hello-shinyjson): migrate Button from Shiny internals to useShinyInput

Replace direct access to window.Shiny.shinyapp.\$inputValues with the
useShinyInput hook for the action button increment pattern."
```

---

### Task 4: Update STATUS.md

**Files:**
- Modify: `STATUS.md`

- [ ] **Step 1: Update the examples table description for 1-hello-world**

In `STATUS.md`, find this line in the examples table:

```
| 1-hello-world | 8761 | Working | Text input/output with useShinyInput/useShinyOutput |
```

Replace with:

```
| 1-hello-world | 8761 | Working | Decomposed components (Card, TextInput, Divider, OutputDisplay) composed from Python via Spec |
```

- [ ] **Step 2: Add recent fixes entries**

At the end of the `### Recent fixes` section, add:

```markdown
- **Hello world decomposition**: Replaced monolithic `HelloWorldComponent` with five small registered components (`Card`, `Heading`, `TextInput`, `Divider`, `OutputDisplay`). Python now composes the full UI tree via `Spec` instead of delegating to a single JS component.
- **Button hook migration (hello-shinyjson)**: Migrated `Button` component from private Shiny internals (`window.Shiny.shinyapp.$inputValues`) to `useShinyInput` hook.
```

- [ ] **Step 3: Commit**

```bash
git add STATUS.md
git commit -m "docs: update STATUS.md with hello world decomposition and Button fix"
```

---

### Task 5: Manual smoke test

No file changes in this task — verification only.

- [ ] **Step 1: Run the 1-hello-world example**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/quito && uv run shiny run examples/1-hello-world/app.py --port 8761`

Verify in the browser at `http://localhost:8761`:
1. Card appears with "Hello Shiny React!" title
2. Text input shows "Hello, world!" as default value
3. Typing in the input sends the value to the server
4. The output display shows the uppercased text from the server
5. A horizontal divider separates the input from the output

- [ ] **Step 2: Run the hello-shinyjson example**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/quito && uv run shiny run examples/hello-shinyjson/app.py --port 8765`

Verify in the browser at `http://localhost:8765`:
1. Card renders with title from the text input
2. Badges render with count from the slider
3. **Button clicks increment** — the "Button Clicks" counter in "Input Values" should increase on each click
4. No console errors about `$inputValues` or `setInputValue`

- [ ] **Step 3: Run Python checks**

Run: `cd /Users/barret/conductor/workspaces/shinyjson.nosync/quito && make py-format`

Expected: No formatting changes needed (files already formatted).
