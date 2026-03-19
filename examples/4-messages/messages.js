// Messages example — registers with shinyjson to demonstrate
// useShinyMessageHandler hook for server-to-client messaging.
(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useState = React.useState;
  var useShinyMessageHandler = window.shinyjson.useShinyMessageHandler;

  function App() {
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
      { className: "app-container" },
      h("h1", null, "Event Message Demo"),
      h(
        "div",
        { className: "card" },
        h("h2", null, "Toast messages from server"),
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
      )
    );
  }

  window.shinyjson.registerComponents(null, {
    App: App,
  });
})();
