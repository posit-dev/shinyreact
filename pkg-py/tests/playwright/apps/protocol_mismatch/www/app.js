const { React, ReactDOM, useShinyInput } = window.shinyreact;
const h = React.createElement;

// Any hook mount runs the handshake, which throws here. This text is never
// expected on screen — the fatal banner replaces it.
function App() {
  const [txt] = useShinyInput("txt", "");
  return h("p", { "data-testid": "body" }, `this should not render: ${txt}`);
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
