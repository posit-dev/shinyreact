const { useShinyInput, useShinyOutput, useShinyInitialized, ReactDOM } =
  window.shinyjson;

function App() {
  const initialized = useShinyInitialized();
  const [name, setName] = useShinyInput("name", "");
  const [clickCount, setClickCount] = useShinyInput("click_count", 0, {
    debounceMs: 0,
    priority: "event",
  });
  const [data] = useShinyOutput("greeting_data", null);

  if (!initialized) {
    return null;
  }

  return (
    <div style={{ fontFamily: "system-ui", maxWidth: "400px", margin: "2rem auto" }}>
      <h1>SPA Hello World</h1>
      <label htmlFor="name-input">Your name:</label>
      <input
        id="name-input"
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={{
          display: "block",
          width: "100%",
          padding: "0.5rem",
          marginTop: "0.25rem",
          marginBottom: "1rem",
          fontSize: "1rem",
          border: "1px solid #ccc",
          borderRadius: "4px",
        }}
      />
      <button
        onClick={() => setClickCount(clickCount + 1)}
        style={{
          padding: "0.5rem 1rem",
          fontSize: "1rem",
          cursor: "pointer",
          marginBottom: "1rem",
        }}
      >
        Click me
      </button>
      <div style={{ padding: "1rem", background: "#f0f0f0", borderRadius: "8px" }}>
        {data ? (
          <>
            <p style={{ fontSize: "1.25rem", margin: 0 }}>{data.greeting}</p>
            <p style={{ color: "#666", margin: "0.5rem 0 0 0" }}>
              Button clicked {data.count} times
            </p>
          </>
        ) : (
          <>
            <p style={{ fontSize: "1.25rem", margin: 0 }}>{"\u00A0"}</p>
            <p style={{ margin: "0.5rem 0 0 0" }}>{"\u00A0"}</p>
          </>
        )}
      </div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
