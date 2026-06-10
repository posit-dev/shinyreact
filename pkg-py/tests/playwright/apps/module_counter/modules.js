(function () {
  var React = window.shinyreact.React;
  var h = React.createElement;
  var useShinyInput = window.shinyreact.useShinyInput;
  var useShinyOutputValue = window.shinyreact.useShinyOutputValue;
  var ShinyModuleProvider = window.shinyreact.ShinyModuleProvider;

  function Container(args) {
    return h("div", null, args.children);
  }

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

  function Counter(args) {
    var ns = args.element.props.namespace;
    return h(
      ShinyModuleProvider,
      { namespace: ns },
      h(CounterBody, { namespace: ns }),
    );
  }

  window.shinyreact.registerComponents(null, {
    Container: Container,
    Counter: Counter,
  });
})();
