// Bookmarking example — demonstrates RestoreContext flowing into React inputs.
(function () {
  var React = window.shinyreact.React;
  var ReactDOM = window.shinyreact.ReactDOM;
  var h = React.createElement;
  var useShinyInput = window.shinyreact.useShinyInput;
  var useShinyOutputValue = window.shinyreact.useShinyOutputValue;
  var useSetShinyInput = window.shinyreact.useSetShinyInput;

  function App() {
    var txt = useShinyInput("txt", "");
    var num = useShinyInput("num", 0);
    var chk = useShinyInput("chk", false);
    var bookmarkClicks = useSetShinyInput("bookmark_clicks", 0, {
      debounceMs: 0,
      priority: "event",
    });
    var greeting = useShinyOutputValue("greeting", "");
    var clickCount = React.useRef(0);

    function handleBookmark() {
      clickCount.current += 1;
      bookmarkClicks(clickCount.current);
    }

    return h(
      "div",
      null,
      h("h1", null, "Bookmarking demo"),
      h(
        "p",
        { className: "note" },
        "Edit the inputs, click 'Bookmark', then copy the URL and open it in a new tab.",
      ),
      h(
        "div",
        { className: "card" },
        h("label", null, "Text"),
        h("input", {
          type: "text",
          value: txt[0],
          onChange: function (e) {
            txt[1](e.target.value);
          },
        }),
      ),
      h(
        "div",
        { className: "card" },
        h("label", null, "Number"),
        h("input", {
          type: "number",
          value: num[0],
          onChange: function (e) {
            num[1](Number(e.target.value));
          },
        }),
      ),
      h(
        "div",
        { className: "card" },
        h("label", null, "Checkbox"),
        h("input", {
          type: "checkbox",
          checked: chk[0],
          onChange: function (e) {
            chk[1](e.target.checked);
          },
        }),
      ),
      h(
        "div",
        { className: "card" },
        h("div", { className: "output" }, "Server says: ", greeting),
      ),
      h(
        "button",
        { onClick: handleBookmark, "data-testid": "bookmark-btn" },
        "Bookmark",
      ),
    );
  }

  // No mount div in the generated page -- create the container and append it
  // to <body>. The script is deferred, so document.body is parsed by now.
  ReactDOM.createRoot(
    document.body.appendChild(document.createElement("div")),
  ).render(h(App));
})();
