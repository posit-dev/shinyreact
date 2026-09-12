# shinyreact <a href="https://posit-dev.github.io/shinyreact/"><img src="docs/logo.svg" align="right" height="138" alt="shinyreact website" /></a>

<!-- badges: start -->
[![check-py](https://github.com/posit-dev/shinyreact/actions/workflows/check-py.yaml/badge.svg)](https://github.com/posit-dev/shinyreact/actions/workflows/check-py.yaml)
<!-- badges: end -->

shinyreact lets you write the UI of a [Shiny for Python](https://shiny.posit.co/py/) app as a [React](https://react.dev/) client you own, while the Python server contains only reactive computation. It provides the bridge between the two and ships zero UI components itself. The same [JavaScript bundle](https://posit-dev.github.io/shinyreact/js/) backs the [R package](https://posit-dev.github.io/shinyreact/r/), so one React client works against an `app.py` or an `app.R` server. The [full site](https://posit-dev.github.io/shinyreact/) covers all three.

## Installation

shinyreact is not yet on PyPI. Install the development version from GitHub:

```bash
pip install "git+https://github.com/posit-dev/shinyreact.git"
```

## Usage

`set_react_page()` discovers `www/ui.js` (and `www/ui.css`, if present) next to the app file and serves them as the page. `@reactive_output` publishes any JSON-serializable value to the client's `useShinyOutputValue()` hook:

```python
from shiny.express import input
from shinyreact import reactive_output, set_react_page

set_react_page()


@reactive_output
def greeting():
    return f"Hello, {input.name()}!"
```

In Core mode, `page_react()` is the `ui` argument instead:

```python
from shiny import App
from shinyreact import page_react, reactive_output


def server(input, output, session):
    @reactive_output
    def greeting():
        return f"Hello, {input.name()}!"


app = App(page_react(), server)
```

The matching `www/ui.js`:

```js
const { React, ReactDOM, useShinyInput, useShinyOutputValue } = window.shinyreact;
const h = React.createElement;

function App() {
  const [name, setName] = useShinyInput("name", "world");
  const greeting = useShinyOutputValue("greeting");
  return h(
    "div",
    null,
    h("input", { value: name, onChange: (e) => setName(e.target.value) }),
    h("p", null, greeting)
  );
}

ReactDOM.createRoot(document.body.appendChild(document.createElement("div"))).render(h(App));
```

Try a complete app:

```bash
git clone https://github.com/posit-dev/shinyreact
shiny run shinyreact/examples/01-hello/app.py
```

## Learn more

- [Get started](https://posit-dev.github.io/shinyreact/) walks through the `ui.tsx` pattern: inputs, outputs, messages, and embedding traditional Shiny renderers.
- [TSX files and JavaScript build tools](https://posit-dev.github.io/shinyreact/articles/tsx-and-build-tools.html) explains `.tsx`, JSX, TypeScript, and what `npm run build` does.
- [Client hooks](https://posit-dev.github.io/shinyreact/articles/hooks.html) lists everything at `window.shinyreact`.
- [Testing](https://posit-dev.github.io/shinyreact/articles/testing.html) covers shiny's `local_server` pytest fixture for driving a server with no browser, and `WireTap` for wire payloads in Playwright tests.
- [Agent Skills](https://posit-dev.github.io/shinyreact/articles/agent-skills.html) explains the skills that ship with the package for coding agents.
- The [examples catalog](https://github.com/posit-dev/shinyreact/blob/main/examples/README.md) lists runnable apps from no-build to Vite + HMR.
