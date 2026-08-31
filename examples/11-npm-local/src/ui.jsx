import { useShinyInput, useShinyOutputStatus, useShinyOutputValue } from "@posit/shinyreact";
import "@posit/shinyreact/styles";
import { createRoot } from "react-dom/client";

import "./ui.css";

// The import above is the whole point of this example: the hooks come from
// the `@posit/shinyreact` package that shipped inside the installed
// shinyreact server package (see this example's README), not from the
// registry and not from `window.shinyreact`.

function Histogram({ data, dim }) {
  const { breaks, counts } = data;
  const max = Math.max(...counts, 1);
  const [w, h] = [620, 320];
  return (
    <svg
      className={dim ? "recalculating" : ""}
      viewBox={`0 0 ${w} ${h}`}
      role="img"
      aria-label={`Histogram of Old Faithful waiting times in ${counts.length} bins`}
    >
      {counts.map((count, i) => {
        const x0 = (i / counts.length) * w;
        const x1 = ((i + 1) / counts.length) * w;
        const barHeight = (count / max) * (h - 8);
        return (
          <rect
            key={breaks[i]}
            x={x0}
            y={h - barHeight}
            width={Math.max(x1 - x0 - 1, 1)}
            height={barHeight}
            fill="#447099"
          />
        );
      })}
    </svg>
  );
}

function App() {
  const [bins, setBins] = useShinyInput("bins", 30);
  const data = useShinyOutputValue("dist_data");
  const caption = useShinyOutputValue("dist_caption");
  const status = useShinyOutputStatus("dist_data");

  return (
    <main>
      <h1>Old Faithful</h1>
      <label htmlFor="bins">Number of bins: {bins}</label>
      <input
        id="bins"
        type="range"
        min="1"
        max="50"
        value={bins}
        onChange={(e) => setBins(Number(e.target.value))}
      />
      {/* Keep the chart mounted while the server recalculates — dim it instead. */}
      {data ? (
        <Histogram data={data} dim={status === "recalculating"} />
      ) : (
        <div className="placeholder">Loading…</div>
      )}
      <p>{caption ?? " "}</p>
    </main>
  );
}

createRoot(document.body.appendChild(document.createElement("div"))).render(<App />);
