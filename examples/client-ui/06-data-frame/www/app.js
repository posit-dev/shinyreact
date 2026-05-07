const { React, ReactDOM, useShinyInput, useShinyOutput, useShinyInitialized, ShinyOutput } =
  window.shinyreact;

const h = React.createElement;

function App() {
  const initialized = useShinyInitialized();
  const [rowCount, setRowCount] = useShinyInput("row_count", 5);
  const [greeting] = useShinyOutput("greeting", null);

  if (!initialized) return null;

  return h(
    "div",
    { style: { fontFamily: "system-ui", maxWidth: "800px", margin: "2rem auto" } },
    h("h1", null, "Data Frame in React"),
    h("p", null, greeting),
    h("label", { htmlFor: "row-count" }, "Number of rows: "),
    h("input", {
      id: "row-count",
      type: "range",
      min: 1,
      max: 20,
      value: rowCount,
      onChange: (e) => setRowCount(Number(e.target.value)),
      style: { marginLeft: "0.5rem" },
    }),
    h("span", { style: { marginLeft: "0.5rem" } }, rowCount),
    h(
      "div",
      { style: { marginTop: "1rem" } },
      h(ShinyOutput, { id: "my_table", tagName: "shiny-data-frame" }),
    ),
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(h(App));
