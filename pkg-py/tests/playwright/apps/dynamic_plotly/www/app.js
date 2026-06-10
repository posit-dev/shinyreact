const { React, ReactDOM, useShinyInitialized, useShinyInput, ShinyOutput } =
  window.shinyreact;
const h = React.createElement;

function App() {
  // Both hooks run on every render (Rules of Hooks); the early return below
  // is safe because no hooks follow it.
  const initialized = useShinyInitialized();
  const [show, setShow] = useShinyInput("show", false, { debounceMs: 0, priority: "event" });
  if (!initialized) return null;

  return h(
    "div",
    { "data-test": "container" },
    h("input", {
      type: "checkbox",
      id: "show",
      checked: show,
      onChange: (e) => setShow(e.target.checked),
    }),
    // Hosts Shiny's dynamic @render.ui output; bindAll lets Shiny inject the
    // dependency for whatever the dynamic UI renders.
    h(ShinyOutput, { id: "holder", className: "shiny-html-output" }),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
