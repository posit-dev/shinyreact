const { React, useShinyInput, useShinyOutput, useShinyInitialized, ReactDOM } =
  window.shinyjson;

const COLUMNS = ["A", "B", "C"];

function App() {
  const initialized = useShinyInitialized();
  const [moveItem, setMoveItem] = useShinyInput("move_item", null, {
    debounceMs: 0,
    priority: "event",
  });
  const [data] = useShinyOutput("column_data", null);

  if (!initialized) return null;

  function handleMove(item, fromCol, toCol) {
    setMoveItem({ item, from: fromCol, to: toCol });
  }

  return (
    <div style={{ fontFamily: "system-ui", maxWidth: "700px", margin: "2rem auto" }}>
      <h2>Move Items Between Columns</h2>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
        {COLUMNS.map((col, colIdx) => (
          <div key={col}>
            <h4>Column {col}</h4>
            {data && data[col] && data[col].length > 0 ? (
              data[col].map((item) => (
                <div
                  key={item}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    padding: "0.5rem",
                    marginBottom: "0.5rem",
                    border: "1px solid #ccc",
                    borderRadius: "4px",
                  }}
                >
                  <span style={{ flex: 1 }}>{item}</span>
                  {colIdx > 0 && (
                    <button onClick={() => handleMove(item, col, COLUMNS[colIdx - 1])}>
                      ←
                    </button>
                  )}
                  {colIdx < COLUMNS.length - 1 && (
                    <button onClick={() => handleMove(item, col, COLUMNS[colIdx + 1])}>
                      →
                    </button>
                  )}
                </div>
              ))
            ) : (
              <p style={{ color: "#999" }}>(empty)</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
