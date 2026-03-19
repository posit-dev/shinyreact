// Modules example — three independent counter widgets with Shiny module namespaces
(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useState = React.useState;
  var useRef = React.useRef;
  var useShinyInput = window.shinyjson.useShinyInput;
  var useShinyOutput = window.shinyjson.useShinyOutput;
  var useShinyMessageHandler = window.shinyjson.useShinyMessageHandler;
  var ShinyModuleProvider = window.shinyjson.ShinyModuleProvider;

  function CounterWidget(props) {
    var label = props.label;

    var inputResult = useShinyInput("count", 0);
    var count = inputResult[0];
    var setCount = inputResult[1];

    var outputResult = useShinyOutput("serverCount", 0);
    var serverCount = outputResult[0];

    var doubledResult = useShinyOutput("serverDoubled", 0);
    var serverDoubled = doubledResult[0];

    var notificationState = useState(null);
    var notification = notificationState[0];
    var setNotification = notificationState[1];
    var timerRef = useRef(null);

    useShinyMessageHandler("notification", function (data) {
      if (timerRef.current) clearTimeout(timerRef.current);
      setNotification(data.message);
      timerRef.current = setTimeout(function () {
        setNotification(null);
        timerRef.current = null;
      }, 3000);
    });

    return h(
      "div",
      { className: "counter-widget" },
      h("h3", null, label),
      h(
        "div",
        { className: "counter-content" },
        h(
          "div",
          { className: "counter-display" },
          h(
            "div",
            { className: "counter-value" },
            h("span", { className: "label" }, "Client count:"),
            h("span", { className: "value" }, count)
          ),
          h(
            "div",
            { className: "counter-value" },
            h("span", { className: "label" }, "Server count:"),
            h("span", { className: "value" }, serverCount)
          ),
          h(
            "div",
            { className: "counter-value" },
            h("span", { className: "label" }, "Server doubled:"),
            h("span", { className: "value" }, serverDoubled)
          )
        ),
        h(
          "button",
          {
            className: "increment-button",
            onClick: function () {
              setCount(count + 1);
            },
          },
          "Increment"
        ),
        notification
          ? h("div", { className: "notification" }, notification)
          : null
      )
    );
  }

  function App() {
    return h(
      "div",
      { className: "app-container" },
      h(
        "header",
        { className: "app-header" },
        h("h1", null, "Shiny Module Namespace Demo"),
        h(
          "p",
          { className: "subtitle" },
          "Three independent counter widgets, each in its own namespace"
        )
      ),
      h(
        "div",
        { className: "widgets-grid" },
        h(
          ShinyModuleProvider,
          { namespace: "counter1" },
          h(CounterWidget, { label: "Counter 1" })
        ),
        h(
          ShinyModuleProvider,
          { namespace: "counter2" },
          h(CounterWidget, { label: "Counter 2" })
        ),
        h(
          ShinyModuleProvider,
          { namespace: "counter3" },
          h(CounterWidget, { label: "Counter 3" })
        )
      ),
      h(
        "div",
        { className: "info-section" },
        h("h2", null, "How It Works"),
        h(
          "p",
          null,
          "Each counter widget is wrapped in a ",
          h("code", null, "ShinyModuleProvider"),
          " with a unique namespace. This allows multiple instances of the same component to operate independently without ID conflicts."
        ),
        h(
          "ul",
          null,
          h(
            "li",
            null,
            h("strong", null, "Counter 1"),
            " uses namespace ",
            h("code", null, "counter1")
          ),
          h(
            "li",
            null,
            h("strong", null, "Counter 2"),
            " uses namespace ",
            h("code", null, "counter2")
          ),
          h(
            "li",
            null,
            h("strong", null, "Counter 3"),
            " uses namespace ",
            h("code", null, "counter3")
          )
        ),
        h(
          "p",
          null,
          "On the server side, Shiny modules automatically namespace the outputs and messages, keeping each widget's state completely separate."
        )
      )
    );
  }

  window.shinyjson.registerComponents(null, {
    App: App,
  });
})();
