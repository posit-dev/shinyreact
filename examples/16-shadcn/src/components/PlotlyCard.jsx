import { useEffect, useRef } from "react";
import Plotly from "plotly.js-basic-dist-min";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const { useShinyOutput } = window.shinyjson;

function linearFit(xs, ys) {
  const n = xs.length;
  const sumX = xs.reduce((a, b) => a + b, 0);
  const sumY = ys.reduce((a, b) => a + b, 0);
  const sumXY = xs.reduce((a, x, i) => a + x * ys[i], 0);
  const sumXX = xs.reduce((a, x) => a + x * x, 0);
  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

export function PlotlyCard() {
  const ref = useRef(null);
  const [data] = useShinyOutput("scatter_data", null);

  useEffect(() => {
    if (!ref.current || !data?.age?.length) return;

    const xs = data.age;
    const ys = data.score;
    const { slope, intercept } = linearFit(xs, ys);
    const xMin = Math.min(...xs);
    const xMax = Math.max(...xs);
    const trendX = [xMin, xMax];
    const trendY = trendX.map((x) => slope * x + intercept);

    Plotly.react(
      ref.current,
      [
        {
          x: xs,
          y: ys,
          mode: "markers",
          type: "scatter",
          name: "Observations",
          marker: { size: 10, opacity: 0.7 },
        },
        {
          x: trendX,
          y: trendY,
          mode: "lines",
          type: "scatter",
          name: "Trend",
          line: { color: "#dc2626", dash: "dash", width: 2 },
        },
      ],
      {
        margin: { l: 48, r: 16, t: 8, b: 40 },
        xaxis: { title: { text: "Age" } },
        yaxis: { title: { text: "Score" } },
        showlegend: false,
      },
      { displayModeBar: false, responsive: true },
    );

    const el = ref.current;
    return () => {
      Plotly.purge(el);
    };
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Plotly Output (client-side)</CardTitle>
      </CardHeader>
      <CardContent>
        <div ref={ref} className="w-full min-h-[300px]" />
      </CardContent>
    </Card>
  );
}
