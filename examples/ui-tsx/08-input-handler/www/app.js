const { React, ReactDOM, useShinyInput, useShinyOutputValue, useShinyInitialized } =
  window.shinyreact;

const h = React.createElement;

function App() {
  const initialized = useShinyInitialized();
  const [when, setWhen] = useShinyInput(
    "when",
    Math.floor(Date.now() / 1000),
    { type: "shiny.datetime", debounceMs: 0 },
  );
  const echoed = useShinyOutputValue("when_info");

  if (!initialized) return null;

  return h(
    "div",
    { className: "card" },
    h("h2", null, "Input handler — `shiny.datetime`"),
    h(
      "p",
      null,
      "The client sends a unix-seconds number. The server's `shiny.datetime` handler ",
      "coerces it to a Python `datetime` before `input.when()` resolves. Toggle the ",
      "input or change the number to see the round-trip.",
    ),
    h(
      "label",
      { className: "row" },
      h("span", null, "Unix seconds:"),
      h("input", {
        type: "number",
        value: when,
        onChange: (e) => setWhen(Number(e.target.value)),
      }),
    ),
    h(
      "p",
      { className: "echo" },
      "Server saw: ",
      h("code", null, echoed ?? "…"),
    ),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
