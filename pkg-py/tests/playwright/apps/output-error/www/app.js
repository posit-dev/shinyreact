const {
  React,
  ReactDOM,
  useShinyInput,
  useShinyOutputError,
  useShinyOutputStatus,
  useShinyOutputValue,
} = window.shinyreact;

const h = React.createElement;

function App() {
  const [n, setN] = useShinyInput("n", 1, { debounceMs: 0 });
  const value = useShinyOutputValue("answer");
  const status = useShinyOutputStatus("answer");
  const error = useShinyOutputError("answer");

  return h(
    "div",
    { "data-test": "container" },
    h("input", {
      "data-test": "input",
      type: "number",
      value: n,
      onChange: (e) => setN(Number(e.target.value)),
    }),
    h("span", { "data-test": "value" }, value ?? ""),
    h("span", { "data-test": "status" }, status),
    h("span", { "data-test": "error" }, error ? error.message : ""),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
