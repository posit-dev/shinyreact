const { React, ReactDOM, useSetShinyInput } = window.shinyreact;
const h = React.createElement;

function App() {
  const setClicks = useSetShinyInput("bookmark_clicks", 0, {
    debounceMs: 0,
    priority: "event",
  });
  return h(
    "button",
    { "data-testid": "bookmark-btn", onClick: () => setClicks(1) },
    "Bookmark",
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
