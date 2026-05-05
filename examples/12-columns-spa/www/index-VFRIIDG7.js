(() => {
  // src/react-shim.js
  var React = window.shinyjson.React;

  // src/App.jsx
  var { React: React2, useShinyInput, useShinyOutput, useShinyInitialized, ReactDOM } = window.shinyjson;
  var COLUMNS = ["A", "B", "C"];
  function App() {
    const initialized = useShinyInitialized();
    const [moveItem, setMoveItem] = useShinyInput("move_item", null, {
      debounceMs: 0,
      priority: "event"
    });
    const [data] = useShinyOutput("column_data", null);
    if (!initialized) return null;
    function handleMove(item, fromCol, toCol) {
      setMoveItem({ item, from: fromCol, to: toCol });
    }
    return /* @__PURE__ */ React2.createElement("div", { style: { fontFamily: "system-ui", maxWidth: "700px", margin: "2rem auto" } }, /* @__PURE__ */ React2.createElement("h2", null, "Move Items Between Columns"), /* @__PURE__ */ React2.createElement("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" } }, COLUMNS.map((col, colIdx) => /* @__PURE__ */ React2.createElement("div", { key: col }, /* @__PURE__ */ React2.createElement("h4", null, "Column ", col), data && data[col] && data[col].length > 0 ? data[col].map((item) => /* @__PURE__ */ React2.createElement(
      "div",
      {
        key: item,
        style: {
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          padding: "0.5rem",
          marginBottom: "0.5rem",
          border: "1px solid #ccc",
          borderRadius: "4px"
        }
      },
      /* @__PURE__ */ React2.createElement("span", { style: { flex: 1 } }, item),
      colIdx > 0 && /* @__PURE__ */ React2.createElement("button", { onClick: () => handleMove(item, col, COLUMNS[colIdx - 1]) }, "\u2190"),
      colIdx < COLUMNS.length - 1 && /* @__PURE__ */ React2.createElement("button", { onClick: () => handleMove(item, col, COLUMNS[colIdx + 1]) }, "\u2192")
    )) : /* @__PURE__ */ React2.createElement("p", { style: { color: "#999" } }, "(empty)")))));
  }
  var root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(/* @__PURE__ */ React2.createElement(App, null));
})();
