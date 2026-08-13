(function () {
  var React = window.shinyreact.React;
  var ReactDOM = window.shinyreact.ReactDOM;
  var h = React.createElement;
  var useShinyInput = window.shinyreact.useShinyInput;
  var useShinyOutputValue = window.shinyreact.useShinyOutputValue;
  var ShinyModuleProvider = window.shinyreact.ShinyModuleProvider;

  function CounterBody(props) {
    var inputResult = useShinyInput("count", 0);
    var count = inputResult[0];
    var setCount = inputResult[1];
    var serverCount = useShinyOutputValue("serverCount", 0);

    return h(
      "div",
      { className: "counter", "data-test-namespace": props.namespace },
      h("span", { className: "value" }, String(serverCount)),
      h(
        "button",
        {
          className: "increment",
          onClick: function () {
            setCount(count + 1);
          },
        },
        "Increment",
      ),
    );
  }

  function Counter(props) {
    return h(
      ShinyModuleProvider,
      { namespace: props.namespace },
      h(CounterBody, { namespace: props.namespace }),
    );
  }

  function App() {
    return h(
      "div",
      null,
      h(Counter, { namespace: "a" }),
      h(Counter, { namespace: "b" }),
    );
  }

  ReactDOM.createRoot(document.getElementById("root")).render(h(App));
})();
