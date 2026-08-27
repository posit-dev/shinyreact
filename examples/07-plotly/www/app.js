const { React, ReactDOM, useShinyInput, useShinyOutputValue, useShinyInitialized, ShinyOutput } =
  window.shinyreact;

const h = React.createElement;

function App() {
  const initialized = useShinyInitialized();
  const [numPoints, setNumPoints] = useShinyInput("num_points", 50);
  const greeting = useShinyOutputValue("greeting", null);

  if (!initialized) return null;

  return h(
    "div",
    { style: { fontFamily: "system-ui", maxWidth: "900px", margin: "2rem auto" } },
    h("h1", null, "Plotly in React"),
    h("p", null, greeting),
    h("label", { htmlFor: "num-points" }, "Number of points: "),
    h("input", {
      id: "num-points",
      type: "range",
      min: 10,
      max: 500,
      value: numPoints,
      onChange: (e) => setNumPoints(Number(e.target.value)),
      style: { marginLeft: "0.5rem" },
    }),
    h("span", { style: { marginLeft: "0.5rem" } }, numPoints),
    h(
      "div",
      { style: { marginTop: "1rem", height: "400px" } },
      h(ShinyOutput, {
        id: "scatter",
        // One client, two servers: "shiny-ipywidget-output" is what Python's
        // shinywidgets binding looks for; "plotly html-widget
        // html-widget-output" is what R's htmlwidgets binding looks for
        // (mirrors plotly::plotlyOutput()). Whichever server runs, only its
        // binding JS is loaded, so the other side's classes are inert.
        className:
          "shiny-ipywidget-output plotly html-widget html-widget-output shiny-report-size",
        style: { width: "100%", height: "100%" },
      }),
    ),
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(h(App));
