const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(
    "div",
    { "data-test": "container" },
    // Plotly renders 0×0 without explicit sizing on the host element.
    h(ShinyOutput, {
      id: "scatter",
      className: "shiny-ipywidget-output shiny-report-size",
      style: { width: "100%", height: "300px" },
    }),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
