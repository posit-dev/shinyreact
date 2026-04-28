const { useShinyInput, useShinyOutput, useShinyInitialized, ReactDOM } =
  window.shinyjson;

function OutputCard({ label, title, count }) {
  return (
    <div
      style={{
        padding: "1rem",
        background: "#f0f0f0",
        borderRadius: "8px",
        marginBottom: "1rem",
      }}
    >
      <p
        style={{
          fontSize: "0.75rem",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          color: "#888",
          margin: "0 0 0.5rem 0",
        }}
      >
        {label}
      </p>
      <p style={{ fontSize: "1.25rem", margin: 0 }}>
        {title != null ? title : " "}
      </p>
      <p style={{ color: "#666", margin: "0.5rem 0 0 0" }}>
        {count != null ? `Count: ${count}` : " "}
      </p>
    </div>
  );
}

function App() {
  const initialized = useShinyInitialized();
  const [name, setName] = useShinyInput("name", "");
  const [clickCount, setClickCount] = useShinyInput("click_count", 0, {
    debounceMs: 0,
    priority: "event",
  });
  const [serverTitle] = useShinyOutput("txtout_title", null);
  const [serverCount] = useShinyOutput("txtout_count", null);

  if (!initialized) {
    return null;
  }

  const clientTitle = `Hello, ${name || "World"}!`;

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
        Click me ({clickCount})
      </button>
      <hr style={{ border: "none", borderTop: "1px solid #ddd", margin: "1.5rem 0" }} />
      <OutputCard label="Client" title={clientTitle} count={clickCount} />
      <OutputCard label="Server" title={serverTitle} count={serverCount} />
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
