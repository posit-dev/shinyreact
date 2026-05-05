import { useEffect, useRef } from "react";
import Plotly from "plotly.js-basic-dist-min";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const { useShinyInput, useShinyOutput } = window.shinyreact;

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
  const [, setHoverPoint] = useShinyInput("plotly_hover", null);
  const [, setClickPoint] = useShinyInput("plotly_click", null);
  const [, setDblClickPoint] = useShinyInput("plotly_dblclick", null);
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

    // Continuous hover: convert pixel position to data coords using plotly's
    // internal axis helpers, regardless of whether the cursor is over a point.
    const onMouseMove = (e) => {
      const fullLayout = el._fullLayout;
      if (!fullLayout) return;
      const rect = el.getBoundingClientRect();
      const px = e.clientX - rect.left - fullLayout.xaxis._offset;
      const py = e.clientY - rect.top - fullLayout.yaxis._offset;
      // Bail when the cursor is outside the plot area (negative or past length).
      if (
        px < 0 ||
        py < 0 ||
        px > fullLayout.xaxis._length ||
        py > fullLayout.yaxis._length
      ) {
        return;
      }
      setHoverPoint({
        age: fullLayout.xaxis.p2c(px),
        score: fullLayout.yaxis.p2c(py),
      });
    };
    // Convert a DOM mouse position to {age, score} data coords, or null if the
    // cursor is outside the plot area.
    const eventToDataPoint = (e) => {
      const fullLayout = el._fullLayout;
      if (!fullLayout) return null;
      const rect = el.getBoundingClientRect();
      const px = e.clientX - rect.left - fullLayout.xaxis._offset;
      const py = e.clientY - rect.top - fullLayout.yaxis._offset;
      if (
        px < 0 ||
        py < 0 ||
        px > fullLayout.xaxis._length ||
        py > fullLayout.yaxis._length
      ) {
        return null;
      }
      return {
        age: fullLayout.xaxis.p2c(px),
        score: fullLayout.yaxis.p2c(py),
      };
    };

    // Plotly's drag layer uses setPointerCapture, which swallows the mouseup
    // events the browser needs to detect dblclick — so we count clicks
    // manually within a 300 ms window instead of relying on a native dblclick.
    let pendingClickTimer = null;
    const DBLCLICK_MS = 300;

    const onDomClick = (e) => {
      const point = eventToDataPoint(e);
      if (!point) return;
      setClickPoint(point);

      if (pendingClickTimer != null) {
        clearTimeout(pendingClickTimer);
        pendingClickTimer = null;
        setDblClickPoint(point);
        resetView();
      } else {
        pendingClickTimer = setTimeout(() => {
          pendingClickTimer = null;
        }, DBLCLICK_MS);
      }
    };

    const updateSelectionFromEvent = (ev) => {
      if (!ev?.points?.length) return;
      setSelection(ev.points.map((p) => ({ age: p.x, score: p.y })));
    };
    const onSelecting = updateSelectionFromEvent;
    const onSelected = (ev) => {
      // Plotly fires plotly_selected with no points when the user clicks
      // outside the selection or the selection is otherwise cleared. Treat
      // that as "preserve the previous selection" rather than wiping it.
      updateSelectionFromEvent(ev);
      if (ev?.range?.x && ev?.range?.y) {
        // Zoom into the selection box AND clear the selection state — once we
        // zoom, the dashed selection rectangle is no longer meaningful, and
        // the user expects a clean zoomed view.
        Plotly.relayout(el, {
          "xaxis.range": ev.range.x,
          "yaxis.range": ev.range.y,
          selections: [],
        });
        setSelection(null);
      }
    };

    const resetView = () => {
      Plotly.relayout(el, {
        "xaxis.autorange": true,
        "yaxis.autorange": true,
        selections: [],
      });
      setSelection(null);
    };
    // Track whether the cursor is over the plot so a global Esc handler only
    // fires when the user means it (not while they're typing in the text
    // input card, etc.).
    let mouseInPlot = false;
    const onMouseEnter = () => {
      mouseInPlot = true;
    };
    const onMouseLeave = () => {
      mouseInPlot = false;
    };
    const onKeyDown = (e) => {
      if (e.key === "Escape" && mouseInPlot) {
        e.preventDefault();
        resetView();
      }
    };
    const onRelayout = (ev) => {
      const x0 = ev["xaxis.range[0]"];
      const x1 = ev["xaxis.range[1]"];
      const y0 = ev["yaxis.range[0]"];
      const y1 = ev["yaxis.range[1]"];
      if (x0 != null && x1 != null && y0 != null && y1 != null) {
        setXyRanges({ x: [x0, x1], y: [y0, y1] });
      } else if (
        ev["xaxis.autorange"] ||
        ev["yaxis.autorange"] ||
        ev["xaxis.range"] ||
        ev["yaxis.range"]
      ) {
        const fullLayout = el._fullLayout;
        if (fullLayout) {
          setXyRanges({
            x: fullLayout.xaxis.range.slice(),
            y: fullLayout.yaxis.range.slice(),
          });
        }
      }
    };

    el.addEventListener("mousemove", onMouseMove);
    el.addEventListener("mouseenter", onMouseEnter);
    el.addEventListener("mouseleave", onMouseLeave);
    el.addEventListener("click", onDomClick);
    document.addEventListener("keydown", onKeyDown);
    el.on("plotly_selecting", onSelecting);
    el.on("plotly_selected", onSelected);
    el.on("plotly_relayout", onRelayout);

    return () => {
      el.removeEventListener("mousemove", onMouseMove);
      el.removeEventListener("mouseenter", onMouseEnter);
      el.removeEventListener("mouseleave", onMouseLeave);
      el.removeEventListener("click", onDomClick);
      document.removeEventListener("keydown", onKeyDown);
      if (pendingClickTimer != null) clearTimeout(pendingClickTimer);
      Plotly.purge(el);
    };
  }, [
    data,
    setHoverPoint,
    setClickPoint,
    setDblClickPoint,
    setXyRanges,
    setSelection,
  ]);

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
