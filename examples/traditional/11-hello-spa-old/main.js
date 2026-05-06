var React = window.shinyreact.React;
var ReactDOM = window.shinyreact.ReactDOM;
var h = React.createElement;
var useShinyInput = window.shinyreact.useShinyInput;
var useShinyOutput = window.shinyreact.useShinyOutput;
var useShinyInitialized = window.shinyreact.useShinyInitialized;

function Card(_ref) {
  var title = _ref.title;
  var children = _ref.children;
  return h(
    "div",
    { className: "card" },
    title ? h("h1", null, title) : null,
    children
  );
}

function TextInput(_ref) {
  var inputId = _ref.inputId;
  var defaultValue = _ref.defaultValue;
  var placeholder = _ref.placeholder;
  var label = _ref.label;
  var result = useShinyInput(inputId, defaultValue || "");
  var value = result[0];
  var setValue = result[1];

  return h(
    "div",
    { className: "input-group" },
    label ? h("label", null, label) : null,
    h("input", {
      type: "text",
      value: value,
      onChange: function (e) {
        setValue(e.target.value);
      },
      placeholder: placeholder || "",
    })
  );
}

function OutputDisplay(_ref) {
  var outputId = _ref.outputId;
  var label = _ref.label;
  var result = useShinyOutput(outputId, undefined);
  var value = result[0];

  return h(
    "div",
    { className: "output-section" },
    label ? h("label", { className: "output-label" }, label) : null,
    h("div", { className: "output-content" }, value)
  );
}

function App() {
  var initialized = useShinyInitialized();
  if (!initialized) return null;

  return h(
    Card,
    { title: "Hello SPA!" },
    h(TextInput, {
      inputId: "txtin",
      defaultValue: "Hello, world!",
      placeholder: "Enter your message here...",
      label: "Type something to send to Shiny server:",
    }),
    h("hr"),
    h(OutputDisplay, {
      outputId: "txtout",
      label: "Response from Shiny server:",
    })
  );
}

window.addEventListener("DOMContentLoaded", function () {
  var root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(h(App));
});
