const { React, ReactDOM, useShinyOutputValue, ShinyOutput } = window.shinyreact;
const h = React.createElement;
const { useEffect, useState } = React;

// Test scaffolding, not something an app should do: hold every bindAll pass
// open for 250ms *after* its own DOM scan has started, so `widgets_late`
// below reliably mounts while the pass its siblings share is still in
// flight. Only the settling is delayed — the scan keeps its real timing, so
// what the pass does and does not cover is unchanged. The real window is
// sub-millisecond, which is why the jsdom unit tests have to fake it too.
function slowBindAll() {
  const realBindAll = window.Shiny.bindAll.bind(window.Shiny);
  window.Shiny.bindAll = (scope) =>
    Promise.resolve(realBindAll(scope)).then(
      () => new Promise((resolve) => setTimeout(resolve, 250)),
    );
}

function App() {
  const [showLate, setShowLate] = useState(false);
  const echo = useShinyOutputValue("echo");

  // A second commit: the pass `widgets_a` and `widgets_b` share scanned the
  // parent before this element existed, so reusing it would leave this one
  // unbound forever, and silently.
  useEffect(() => setShowLate(true), []);

  return h(
    "div",
    { "data-test": "container" },
    h(ShinyOutput, { id: "widgets_a", className: "shiny-html-output" }),
    h(ShinyOutput, { id: "widgets_b", className: "shiny-html-output" }),
    showLate &&
      h(ShinyOutput, { id: "widgets_late", className: "shiny-html-output" }),
    h("pre", { id: "echo-view" }, echo ? JSON.stringify(echo) : ""),
  );
}

// `Shiny.bindAll` only exists once Shiny has initialized, which is after
// this deferred script runs — so wait for it, then wrap it, then mount.
function start() {
  if (!window.Shiny || !window.Shiny.bindAll) {
    setTimeout(start, 0);
    return;
  }
  slowBindAll();
  ReactDOM.createRoot(document.getElementById("root")).render(h(App));
}

start();
