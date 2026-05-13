const { React, ReactDOM, useShinyInput, useShinyOutputValue, useShinyInitialized } =
  window.shinyreact;

const h = React.createElement;

function App() {
  const initialized = useShinyInitialized();
  // Fixed initial unix-seconds value so the test's "after typing" assertion
  // has a deterministic starting point.
  const [when, setWhen] = useShinyInput("when", 1700000000, {
    type: "shiny.datetime",
    debounceMs: 0,
  });
  const echoed = useShinyOutputValue("when_info");

  if (!initialized) return null;

  return h(
    "div",
    { "data-test": "container" },
    h("input", {
      "data-test": "input",
      type: "number",
      value: when,
      onChange: (e) => setWhen(Number(e.target.value)),
    }),
    h("span", { "data-test": "echo" }, echoed ?? "pending"),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
