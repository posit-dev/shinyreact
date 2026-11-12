const {
  React,
  ReactDOM,
  useSetShinyInput,
  useShinyBusy,
  useShinyConnected,
  useShinyOutputValue,
} = window.shinyreact;

const h = React.createElement;

function App() {
  const busy = useShinyBusy();
  const connected = useShinyConnected();
  const slow = useShinyOutputValue("slow");
  const setSlow = useSetShinyInput("slow", 0, {
    debounceMs: 0,
    priority: "event",
  });
  const setClose = useSetShinyInput("close", 0, {
    debounceMs: 0,
    priority: "event",
  });

  return h(
    "div",
    null,
    h("button", { "data-test": "slow", onClick: () => setSlow(1) }, "Slow"),
    h("button", { "data-test": "close", onClick: () => setClose(1) }, "Close"),
    h("span", { "data-test": "busy" }, String(busy)),
    h("span", { "data-test": "connected" }, String(connected)),
    h("span", { "data-test": "slow-value" }, slow ?? ""),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
