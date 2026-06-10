const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(ShinyOutput, {
    id: "a-scatter",
    className: "shiny-ipywidget-output shiny-report-size",
    style: { width: "100%", height: "300px" },
  });
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
