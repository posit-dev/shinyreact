# The no-build tier

Use this only when you cannot run `npm` — no toolchain, a locked-down host, or
a requirement that the app ship as one editable file. Otherwise take the Vite
tier: JSX and npm libraries are worth the one-time install.

One file, no `package.json`, no build. Everything comes off the global and `h`
stands in for JSX:

```js
const { React, ReactDOM, useShinyInput, useShinyOutputValue } = window.shinyreact;
const h = React.createElement;

function App() {
  const [bins, setBins] = useShinyInput("bins", 30);
  const data = useShinyOutputValue("dist_data");
  return h("div", null,
    h("input", {
      type: "range", min: 1, max: 50, value: bins,
      onChange: (e) => setBins(Number(e.target.value)),
    }),
    data ? h(Histogram, { data }) : h("p", null, "Loading…"),
  );
}

// No mount div in the generated page — create the container and append it.
// The script is deferred, so document.body is parsed by the time this runs.
const root = ReactDOM.createRoot(
  document.body.appendChild(document.createElement("div")),
);
root.render(h(App));
```

Nesting gets unreadable fast, which is the reason to prefer the Vite tier.

