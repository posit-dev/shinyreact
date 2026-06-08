import { useEffect, useState } from "react";

import { useShinyInitialized, useShinyInput, useShinyOutputValue } from "shiny-bridge";

// Exported component = a Fast Refresh boundary. Editing this file (e.g. the
// heading text below) hot-swaps the component WITHOUT losing `count`.
export default function App() {
  const initialized = useShinyInitialized();
  const [count, setCount] = useState(0);
  const [, setServerCount] = useShinyInput<number>("count", 0, { debounceMs: 0 });
  const doubled = useShinyOutputValue<number>("doubled", null);

  // Push the local count to the Shiny server whenever it changes.
  useEffect(() => {
    setServerCount(count);
  }, [count, setServerCount]);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 480, margin: "3rem auto" }}>
      {/* Edit this heading text while `npm run dev` + `shiny run` are running.
          The heading updates instantly and the count below keeps its value. */}
      <h1>Hot reload demo</h1>
      <p>Shiny initialized: {String(initialized)}</p>
      <button onClick={() => setCount((c) => c + 1)}>Count is {count}</button>
      <p>Server doubled it to: {doubled ?? "…"}</p>
    </main>
  );
}
