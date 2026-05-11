const { React, ReactDOM, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

function App() {
  if (!useShinyInitialized()) return null;
  return h(
    React.Fragment,
    null,
    h("h2", null, "classname fixture"),
    h(
      "p",
      null,
      "A hot-pink outline around the (empty) box below means ShinyOutput is a direct child of its parent — no wrapper between.",
    ),
    h(
      "div",
      { "data-test": "container" },
      h(ShinyOutput, {
        id: "out",
        className: "custom-a custom-b",
        "data-test-marker": "x",
        // Empty output → 0×0 box. Give it a minimum so the outline is visible
        // when running manually; tests assert via to_be_attached(), not visibility.
        style: { display: "block", minHeight: "1.5rem", minWidth: "8rem" },
      }),
    ),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
