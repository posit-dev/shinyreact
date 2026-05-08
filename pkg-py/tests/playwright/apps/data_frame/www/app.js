const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(
    "div",
    { "data-test": "container" },
    h(ShinyOutput, { id: "my_table", tagName: "shiny-data-frame" }),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
