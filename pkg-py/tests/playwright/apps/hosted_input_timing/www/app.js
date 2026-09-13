const { React, ReactDOM, useSetShinyInput, ShinyOutput } = window.shinyreact;
const h = React.createElement;

const eventInput = { debounceMs: 0, priority: "event" };

function App() {
  const show = useSetShinyInput("show", 0, eventInput);
  const bump = useSetShinyInput("bump", 0, eventInput);

  return h(
    "div",
    { "data-test": "container" },
    h("button", { id: "show", onClick: () => show((n) => (n ?? 0) + 1) }, "Render it"),
    h("button", { id: "bump", onClick: () => bump((n) => (n ?? 0) + 1) }, "Bump it"),
    h(ShinyOutput, { id: "late_widget", className: "shiny-html-output" }),
    // Never visible on first paint, so Shiny reports both outputs hidden.
    h(
      "div",
      { id: "hidden-panel" },
      h(ShinyOutput, { id: "suspended_widget", className: "shiny-html-output" }),
      h(ShinyOutput, { id: "unsuspended_widget", className: "shiny-html-output" }),
    ),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
