// Modules example — three independent counter widgets with Shiny module namespaces
(function () {
  var React = window.shinyreact.React;
  var h = React.createElement;
  var useState = React.useState;
  var useRef = React.useRef;
  var useShinyInput = window.shinyreact.useShinyInput;
  var useShinyOutput = window.shinyreact.useShinyOutput;
  var useShinyMessageHandler = window.shinyreact.useShinyMessageHandler;
  var ShinyModuleProvider = window.shinyreact.ShinyModuleProvider;

  // ---------------------------------------------------------------------------
  // AppLayout — registered, invoked from spec
  // ---------------------------------------------------------------------------
  function AppLayout(args) {
    var props = args.element.props;
    return h(
      "div",
      { className: "app-container" },
      h(
        "header",
        { className: "app-header" },
        h("h1", null, props.title),
        props.subtitle
          ? h("p", { className: "subtitle" }, props.subtitle)
          : null
      ),
      args.children
    );
  }

  // ---------------------------------------------------------------------------
  // WidgetsGrid — registered, grid wrapper for children
  // ---------------------------------------------------------------------------
  function WidgetsGrid(args) {
    return h("div", { className: "widgets-grid" }, args.children);
  }

  // ---------------------------------------------------------------------------
  // CounterWidget — internal component (not registered directly)
  // ---------------------------------------------------------------------------
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

  // ---------------------------------------------------------------------------
  // ModuleCounter — registered, wraps CounterWidget in ShinyModuleProvider
  // ---------------------------------------------------------------------------
  function ModuleCounter(args) {
    var props = args.element.props;
    return h(
      ShinyModuleProvider,
      { namespace: props.namespace },
      h(CounterWidget, { label: props.label })
    );
  }

  // ---------------------------------------------------------------------------
  // InfoSection — registered, static "How It Works" content
  // ---------------------------------------------------------------------------
  function InfoSection(args) {
    return h(
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
    );
  }

  window.shinyreact.registerComponents(null, {
    AppLayout: AppLayout,
    WidgetsGrid: WidgetsGrid,
    ModuleCounter: ModuleCounter,
    InfoSection: InfoSection,
  });
})();
