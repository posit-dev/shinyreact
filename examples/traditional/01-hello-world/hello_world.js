// hello_world.js — Registers small, composable components for the
// 1-hello-world example. Each component receives `args` (ComponentRenderProps
// from @json-render/react) and reads configuration from `args.element.props`.
(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useShinyInput = window.shinyjson.useShinyInput;
  var useShinyOutput = window.shinyjson.useShinyOutput;

  // Card: styled container with optional title and children
  function Card(args) {
    var props = args.element.props;
    return h(
      "div",
      { className: "card" },
      props.title ? h("h1", null, props.title) : null,
      args.children
    );
  }


  // Heading: renders h1–h6 based on level prop (default: 1)
  function Heading(args) {
    var props = args.element.props;
    var tag = "h" + (props.level || 1);
    return h(tag, null, props.text || "");
  }

  // TextInput: labeled text input wired to Shiny via useShinyInput
  function TextInput(args) {
    var props = args.element.props;
    var opts = {};
    if (props.debounce_ms !== undefined) { opts.debounceMs = props.debounce_ms; }
    var result = useShinyInput(props.input_id, props.default_value || "", opts);
    var value = result[0];
    var setValue = result[1];

    return h(
      "div",
      { className: "input-group" },
      props.label ? h("label", null, props.label) : null,
      h("input", {
        type: "text",
        value: value,
        onChange: function (e) { setValue(e.target.value); },
        placeholder: props.placeholder || "",
      })
    );
  }

  // Divider: horizontal rule
  function Divider() {
    return h("hr");
  }

  // InputDisplay: shows a Shiny input value client-side (no server round-trip)
  function InputDisplay(args) {
    var props = args.element.props;
    var result = useShinyInput(props.input_id, props.default_value || "");
    var value = result[0];

    return h(
      "div",
      { className: "output-section" },
      props.label
        ? h("label", { className: "output-label" }, props.label)
        : null,
      h("div", { className: "output-content" }, value)
    );
  }

  // OutputDisplay: labeled display area wired to Shiny via useShinyOutput
  function OutputDisplay(args) {
    var props = args.element.props;
    var result = useShinyOutput(props.output_id, undefined);
    var value = result[0];

    return h(
      "div",
      { className: "output-section" },
      props.label
        ? h("label", { className: "output-label" }, props.label)
        : null,
      h("div", { className: "output-content" }, value)
    );
  }

  window.shinyjson.registerComponents(null, {
    Card: Card,
    Heading: Heading,
    TextInput: TextInput,
    Divider: Divider,
    InputDisplay: InputDisplay,
    OutputDisplay: OutputDisplay,
  });
})();
