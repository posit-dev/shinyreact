// demo_components.js — Registers demo components for the hello-shinyjson example.
// Loaded via HTMLDependency after shinyjson.js.

(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useShinyInput = window.shinyjson.useShinyInput;

  // Card: styled container with title prop and children slot
  function Card(args) {
    var props = args.element.props;
    var children = args.children;
    return h(
      "div",
      {
        style: {
          border: "1px solid #e0e0e0",
          borderRadius: "8px",
          padding: "16px",
          margin: "8px 0",
          backgroundColor: "#fff",
          boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        },
      },
      props.title ? h("h2", { style: { margin: "0 0 12px 0", fontSize: "1.25rem" } }, props.title) : null,
      children
    );
  }

  // Badge: small colored label with text and variant props
  function Badge(args) {
    var props = args.element.props;
    var colors = {
      default: { bg: "#e0e0e0", fg: "#333" },
      success: { bg: "#d4edda", fg: "#155724" },
      warning: { bg: "#fff3cd", fg: "#856404" },
      danger: { bg: "#f8d7da", fg: "#721c24" },
      info: { bg: "#d1ecf1", fg: "#0c5460" },
    };
    var variant = props.variant || "default";
    var c = colors[variant] || colors["default"];
    return h(
      "span",
      {
        style: {
          display: "inline-block",
          padding: "4px 10px",
          borderRadius: "12px",
          fontSize: "0.85rem",
          fontWeight: "600",
          backgroundColor: c.bg,
          color: c.fg,
          marginRight: "6px",
        },
      },
      props.text || ""
    );
  }

  // Button: styled button that sends clicks to Shiny via useShinyInput
  function Button(args) {
    var props = args.element.props;
    var result = useShinyInput(props.input_id, 0);
    var count = result[0];
    var setCount = result[1];

    return h(
      "button",
      {
        style: {
          padding: "8px 16px",
          borderRadius: "6px",
          border: "none",
          backgroundColor: props.color || "#4a90d9",
          color: "#fff",
          fontSize: "0.9rem",
          fontWeight: "500",
          cursor: "pointer",
          marginRight: "6px",
        },
        onClick: function () {
          setCount(count + 1);
        },
      },
      props.label || "Button"
    );
  }

  window.shinyjson.registerComponents(null, {
    Card: Card,
    Badge: Badge,
    Button: Button,
  });
})();
