const { React, ReactDOM, useShinyInput, useShinyOutput, useShinyInitialized } =
  window.shinyjson;

const h = React.createElement;

function OutputCard({ label, title, count }) {
  return h(
    "div",
    {
      style: {
        padding: "1rem",
        background: "#f0f0f0",
        borderRadius: "8px",
        marginBottom: "1rem",
      },
    },
    h(
      "p",
      {
        style: {
          fontSize: "0.75rem",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          color: "#888",
          margin: "0 0 0.5rem 0",
        },
      },
      label,
    ),
    h(
      "p",
      { style: { fontSize: "1.25rem", margin: 0 } },
      title != null ? title : " ",
    ),
    h(
      "p",
      { style: { color: "#666", margin: "0.5rem 0 0 0" } },
      count != null ? `Count: ${count}` : " ",
    ),
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

  if (!initialized) return null;

  const clientTitle = `Hello, ${name || "World"}!`;

  return h(
    "div",
    {
      style: { fontFamily: "system-ui", maxWidth: "400px", margin: "2rem auto" },
    },
    h("h1", null, "SPA Hello World"),
    h("label", { htmlFor: "name-input" }, "Your name:"),
    h("input", {
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
        borderRadius: "4px",
      },
    }),
    h(
      "button",
      {
        onClick: () => setClickCount(clickCount + 1),
        style: {
          padding: "0.5rem 1rem",
          fontSize: "1rem",
          cursor: "pointer",
          marginBottom: "1rem",
        },
      },
      `Click me (${clickCount})`,
    ),
    h("hr", {
      style: {
        border: "none",
        borderTop: "1px solid #ddd",
        margin: "1.5rem 0",
      },
    }),
    h(OutputCard, { label: "Client", title: clientTitle, count: clickCount }),
    h(OutputCard, { label: "Server", title: serverTitle, count: serverCount }),
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(h(App));
