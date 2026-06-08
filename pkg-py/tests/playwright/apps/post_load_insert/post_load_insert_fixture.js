// Fixture component for the post-load-insertion seeding e2e test (#120).
// Registers a single Badge component used both in static page chrome
// (Node.tagify() → .shinyreact-static at load) and in a @render.ui output
// inserted over the WebSocket after load.
const { registerComponents, React } = window.shinyreact;

function Badge({ element }) {
  return React.createElement(
    "span",
    { className: "badge", "data-testid": "badge" },
    element.props.text,
  );
}

registerComponents(null, { Badge });
