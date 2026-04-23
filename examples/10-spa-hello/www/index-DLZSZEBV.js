(() => {
  // src/react-shim.js
  var React = window.shinyjson.React;

  // src/App.jsx
  var { useShinyInput, useShinyOutput, useShinyInitialized, ReactDOM } = window.shinyjson;
  function App() {
    const initialized = useShinyInitialized();
    const [name, setName] = useShinyInput("name", "");
    const [clickCount, setClickCount] = useShinyInput("click_count", 0, {
      debounceMs: 0,
      priority: "event"
    });
    const [data] = useShinyOutput("greeting_data", null);
    if (!initialized) {
      return null;
    }
    return /* @__PURE__ */ React.createElement("div", { style: { fontFamily: "system-ui", maxWidth: "400px", margin: "2rem auto" } }, /* @__PURE__ */ React.createElement("h1", null, "SPA Hello World"), /* @__PURE__ */ React.createElement("label", { htmlFor: "name-input" }, "Your name:"), /* @__PURE__ */ React.createElement(
      "input",
      {
        id: "name-input",
        type: "text",
        value: name,
        onChange: (e) => setName(e.target.value),
        style: {
          display: "block",
          width: "100%",
          padding: "0.5rem",
          marginTop: "0.25rem",
          marginBottom: "1rem",
          fontSize: "1rem",
          border: "1px solid #ccc",
          borderRadius: "4px"
        }
      }
    ), /* @__PURE__ */ React.createElement(
      "button",
      {
        onClick: () => setClickCount(clickCount + 1),
        style: {
          padding: "0.5rem 1rem",
          fontSize: "1rem",
          cursor: "pointer",
          marginBottom: "1rem"
        }
      },
      "Click me"
    ), /* @__PURE__ */ React.createElement("div", { style: { padding: "1rem", background: "#f0f0f0", borderRadius: "8px" } }, data ? /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("p", { style: { fontSize: "1.25rem", margin: 0 } }, data.greeting), /* @__PURE__ */ React.createElement("p", { style: { color: "#666", margin: "0.5rem 0 0 0" } }, "Button clicked ", data.count, " times")) : /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("p", { style: { fontSize: "1.25rem", margin: 0 } }, "\xA0"), /* @__PURE__ */ React.createElement("p", { style: { margin: "0.5rem 0 0 0" } }, "\xA0"))));
  }
  var root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(/* @__PURE__ */ React.createElement(App, null));
})();
