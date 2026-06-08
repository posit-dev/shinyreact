// Fixture components for the interleaved static + reactive nesting e2e test.
// Registers two components that the app.py-pattern fixture uses both in static
// page chrome (Node.tagify() → .shinyreact-static) and in a render_react.
const { registerComponents, React } = window.shinyreact;

function Badge({ element }) {
  return React.createElement(
    "span",
    { className: "badge", "data-testid": "badge" },
    element.props.text,
  );
}

function Card({ element, children }) {
  return React.createElement(
    "section",
    { className: "card", "data-testid": "card" },
    React.createElement("h2", null, element.props.title),
    children,
  );
}

registerComponents(null, { Badge, Card });
