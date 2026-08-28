const { React, ReactDOM, useShinyInitialized, useShinyInput, ShinyOutput } =
  window.shinyreact;
const h = React.createElement;

function App() {
  // Both hooks run on every render (Rules of Hooks); the early return below is
  // safe because no hooks follow it.
  const initialized = useShinyInitialized();
  const [add, setAdd] = useShinyInput("add", 0, {
    debounceMs: 0,
    priority: "event",
  });
  if (!initialized) return null;

  return h(
    "div",
    { "data-test": "container" },
    h("button", { id: "add", onClick: () => setAdd(add + 1) }, "Add tab"),
    // The "tab" and its output only exist after the click — on the client and
    // on the server alike, so the binding cannot have been on the page before.
    add > 0
      ? h(ShinyOutput, { id: "grid", tagName: "shiny-data-frame" })
      : null,
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
