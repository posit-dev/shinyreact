// HelloWorldComponent — registers with shinyjson to demonstrate
// useShinyInput/useShinyOutput hooks in a Spec-rendered component.
(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useShinyInput = window.shinyjson.useShinyInput;
  var useShinyOutput = window.shinyjson.useShinyOutput;

  function HelloWorldComponent() {
    var inputResult = useShinyInput("txtin", "Hello, world!");
    var txtin = inputResult[0];
    var setTxtin = inputResult[1];

    var outputResult = useShinyOutput("txtout", undefined);
    var txtout = outputResult[0];

    function handleInputChange(event) {
      setTxtin(event.target.value);
    }

    return h(
      "div",
      { className: "card" },
      h("h1", null, "Hello Shiny React!"),
      h(
        "div",
        { className: "input-group" },
        h("label", null, "Type something to send to Shiny server:"),
        h("input", {
          type: "text",
          value: txtin,
          onChange: handleInputChange,
          placeholder: "Enter your message here...",
        })
      ),
      h("hr"),
      h(
        "div",
        { className: "output-section" },
        h(
          "label",
          { className: "output-label" },
          "Response from Shiny server:"
        ),
        h("div", { className: "output-content" }, txtout)
      )
    );
  }

  window.shinyjson.registerComponents(null, {
    HelloWorldComponent: HelloWorldComponent,
  });
})();
