const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(
    React.Fragment,
    null,
    h("h2", null, "plotly fixture"),
    h(
      "p",
      null,
      "A hot-pink outline around the plotly chart below means ShinyOutput is a direct child of its parent — no wrapper between.",
    ),
    h(
      "div",
      { "data-test": "container" },
      // Plotly renders 0×0 without explicit sizing on the host element.
      h(ShinyOutput, {
        id: "scatter",
        className: "shiny-ipywidget-output shiny-report-size",
        style: { width: "100%", height: "300px" },
      }),
    ),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
