const {
  React,
  ReactDOM,
  useSetShinyInput,
  useShinyOutputValue,
  ShinyOutput,
} = window.shinyreact;
const h = React.createElement;

function App() {
  const bump = useSetShinyInput("bump", 0, {
    debounceMs: 0,
    priority: "event",
  });
  const echo = useShinyOutputValue("echo");

  return h(
    "div",
    { "data-test": "container" },
    // Hosts the server's own widget markup. Shiny's html-output binding runs
    // `initializeInputs()` + `bindAll()` on it, which is what turns the
    // slider markup into a real ionRangeSlider.
    h(ShinyOutput, { id: "widgets", className: "shiny-html-output" }),
    h(
      "button",
      { id: "bump", onClick: () => bump((n) => (n ?? 0) + 1) },
      "Update from server",
    ),
    h("pre", { id: "echo-view" }, echo ? JSON.stringify(echo) : ""),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
