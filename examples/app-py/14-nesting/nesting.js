const { registerComponents, React } = window.shinyreact;

function Badge({ element }) {
  return React.createElement(
    "span",
    { style: { background: "#eef", borderRadius: "6px", padding: "2px 8px" } },
    element.props.text,
  );
}

function Card({ element, children }) {
  return React.createElement(
    "section",
    { style: { border: "1px solid #ccc", borderRadius: "8px", padding: "12px" } },
    React.createElement("h2", null, element.props.title),
    children,
  );
}

registerComponents(null, { Badge, Card });
