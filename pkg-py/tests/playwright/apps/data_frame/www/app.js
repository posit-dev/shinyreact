const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(
    React.Fragment,
    null,
    h("h2", null, "data_frame fixture"),
    h(
      "p",
      null,
      "A hot-pink outline around the data-frame below means ShinyOutput is a direct child of its parent — no wrapper between.",
    ),
    h(
      "div",
      { "data-test": "container" },
      h(ShinyOutput, { id: "my_table", tagName: "shiny-data-frame" }),
    ),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
