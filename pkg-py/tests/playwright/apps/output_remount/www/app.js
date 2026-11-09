const { React, ReactDOM, useShinyInput, useShinyOutputValue } =
  window.shinyreact;
const h = React.createElement;

// The only subscriber to `toggles`: unmounting it empties the registry entry,
// so its hidden output div is cleaned up; remounting manufactures a new one.
function Reader() {
  const value = useShinyOutputValue("toggles");
  return h("span", { "data-test": "value" }, value ?? "");
}

function App() {
  const [toggles, setToggles] = useShinyInput("toggles", 0, {
    debounceMs: 0,
    priority: "event",
  });
  const shown = toggles % 2 === 0;

  return h(
    "div",
    null,
    h(
      "button",
      { "data-test": "toggle", onClick: () => setToggles(toggles + 1) },
      shown ? "Hide" : "Show",
    ),
    shown && h(Reader),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
