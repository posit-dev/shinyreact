// Messages example — registers decomposed components with shinyreact to
// demonstrate useShinyMessageHandler hook for server-to-client messaging.
// Each component receives `args` (ComponentRenderProps) and reads
// configuration from `args.element.props`.
(function () {
  var React = window.shinyreact.React;
  var h = React.createElement;
  var useState = React.useState;
  var useShinyMessageHandler = window.shinyreact.useShinyMessageHandler;

  // AppLayout: top-level container with a title and children slot
  function AppLayout(args) {
    var props = args.element.props;
    return h(
      "div",
      { className: "app-container" },
      h("h1", null, props.title),
      args.children
    );
  }

  // ToastCard: card that listens for logEvent messages and displays toasts
  function ToastCard(args) {
    var props = args.element.props;
    var stateResult = useState([]);
    var toasts = stateResult[0];
    var setToasts = stateResult[1];

    // Handle log events from the server using useShinyMessageHandler hook
    useShinyMessageHandler("logEvent", function (msg) {
      console.log("Received log event message:", msg);
      var newToast = {
        id: Date.now(),
        message: msg.text,
        type: msg.category,
      };
      console.log(newToast);

      setToasts(function (prev) {
        return prev.concat([newToast]);
      });

      // Remove toast after 6 seconds
      setTimeout(function () {
        setToasts(function (prev) {
          return prev.filter(function (toast) {
            return toast.id !== newToast.id;
          });
        });
      }, 6000);
    });

    return h(
      "div",
      { className: "card" },
      h("h2", null, props.title),
      h(
        "div",
        { className: "toast-container" },
        toasts.map(function (toast) {
          return h(
            "div",
            { key: toast.id, className: "toast toast-" + toast.type },
            toast.message
          );
        })
      )
    );
  }

  window.shinyreact.registerComponents(null, {
    AppLayout: AppLayout,
    ToastCard: ToastCard,
  });
})();
