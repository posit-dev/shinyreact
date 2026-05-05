const { React, ReactDOM, useShinyInput, useShinyOutput, useShinyInitialized } =
  window.shinyjson;

const h = React.createElement;

const COLUMNS = ["A", "B", "C"];

function ItemRow({ item, colIdx, onMove }) {
  return h(
    "div",
    {
      style: {
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.5rem",
        marginBottom: "0.5rem",
        border: "1px solid #ccc",
        borderRadius: "4px",
      },
    },
    h("span", { style: { flex: 1 } }, item),
    colIdx > 0 &&
      h(
        "button",
        { onClick: () => onMove(item, COLUMNS[colIdx], COLUMNS[colIdx - 1]) },
        "←",
      ),
    colIdx < COLUMNS.length - 1 &&
      h(
        "button",
        { onClick: () => onMove(item, COLUMNS[colIdx], COLUMNS[colIdx + 1]) },
        "→",
      ),
  );
}

function Column({ name, colIdx, items, onMove }) {
  return h(
    "div",
    null,
    h("h4", null, `Column ${name}`),
    items && items.length > 0
      ? items.map((item) =>
          h(ItemRow, { key: item, item, colIdx, onMove }),
        )
      : h("p", { style: { color: "#999" } }, "(empty)"),
  );
}

function App() {
  const initialized = useShinyInitialized();
  const [, setMoveItem] = useShinyInput("move_item", null, {
    debounceMs: 0,
    priority: "event",
  });
  const [data] = useShinyOutput("column_data", null);

  if (!initialized) return null;

  function handleMove(item, fromCol, toCol) {
    setMoveItem({ item, from: fromCol, to: toCol });
  }

  return h(
    "div",
    {
      style: { fontFamily: "system-ui", maxWidth: "700px", margin: "2rem auto" },
    },
    h("h2", null, "Move Items Between Columns"),
    h(
      "div",
      {
        style: {
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: "1rem",
        },
      },
      COLUMNS.map((col, colIdx) =>
        h(Column, {
          key: col,
          name: col,
          colIdx,
          items: data ? data[col] : null,
          onMove: handleMove,
        }),
      ),
    ),
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(h(App));
