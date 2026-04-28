import { useEffect, useRef } from "react";
import Plotly from "plotly.js-basic-dist-min";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const { useShinyInput, useShinyOutput } = window.shinyjson;

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

function pointFromEvent(ev) {
  if (!ev?.points?.length) return null;
  const p = ev.points[0];
  return { age: p.x, score: p.y };
}

export function PlotlyCard() {
  const ref = useRef(null);
  const [data] = useShinyOutput("scatter_data", null);
  const [, setHoverPoint] = useShinyInput("plotly_hover", null);
  const [, setClickPoint] = useShinyInput("plotly_click", null, {
    debounceMs: 0,
    priority: "event",
  });
  const [, setXyRanges] = useShinyInput("plotly_xy_ranges", null);
  const [, setSelection] = useShinyInput("plotly_selection", null);

  useEffect(() => {
    if (!ref.current || !data?.age?.length) return;

    const xs = data.age;
    const ys = data.score;
    const { slope, intercept } = linearFit(xs, ys);
    const xMin = Math.min(...xs);
    const xMax = Math.max(...xs);
    const trendX = [xMin, xMax];
    const trendY = trendX.map((x) => slope * x + intercept);

    const el = ref.current;
    Plotly.react(
      el,
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
        dragmode: "select",
      },
      { displayModeBar: true, responsive: true },
    ).then(() => {
      // Initial axis ranges from the just-rendered figure.
      const fullLayout = el._fullLayout;
      if (fullLayout) {
        setXyRanges({
          x: fullLayout.xaxis.range.slice(),
          y: fullLayout.yaxis.range.slice(),
        });
      }
    });

    const onHover = (ev) => setHoverPoint(pointFromEvent(ev));
    const onUnhover = () => setHoverPoint(null);
    const onClick = (ev) => setClickPoint(pointFromEvent(ev));
    const onSelected = (ev) =>
      setSelection(
        ev?.points
          ? ev.points.map((p) => ({ age: p.x, score: p.y }))
          : null,
      );
    const onRelayout = (ev) => {
      const x0 = ev["xaxis.range[0]"];
      const x1 = ev["xaxis.range[1]"];
      const y0 = ev["yaxis.range[0]"];
      const y1 = ev["yaxis.range[1]"];
      if (x0 != null && x1 != null && y0 != null && y1 != null) {
        setXyRanges({ x: [x0, x1], y: [y0, y1] });
      } else if (ev["xaxis.autorange"] || ev["yaxis.autorange"]) {
        // Double-click / autorange: re-read computed ranges.
        const fullLayout = el._fullLayout;
        if (fullLayout) {
          setXyRanges({
            x: fullLayout.xaxis.range.slice(),
            y: fullLayout.yaxis.range.slice(),
          });
        }
      }
    };

    el.on("plotly_hover", onHover);
    el.on("plotly_unhover", onUnhover);
    el.on("plotly_click", onClick);
    el.on("plotly_selected", onSelected);
    el.on("plotly_relayout", onRelayout);

    return () => {
      Plotly.purge(el);
    };
  }, [data, setHoverPoint, setClickPoint, setXyRanges, setSelection]);

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
