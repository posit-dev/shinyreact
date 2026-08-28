const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(
    "div",
    { "data-test": "container" },
    // Mounts before the server has even registered `grid` — and long before
    // its binding JS exists on the page.
    h(ShinyOutput, { id: "grid", tagName: "shiny-data-frame" }),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
