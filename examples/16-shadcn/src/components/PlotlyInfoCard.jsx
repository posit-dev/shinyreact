import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const { useShinyInput } = window.shinyjson;

function fmtPair(p) {
  if (!p) return "—";
  return `age=${Number(p.age).toFixed(1)}, score=${Number(p.score).toFixed(2)}`;
}

function fmtRange(r) {
  if (!r) return "—";
  const f = (v) => Number(v).toFixed(1);
  return `x=[${f(r.x[0])}, ${f(r.x[1])}], y=[${f(r.y[0])}, ${f(r.y[1])}]`;
}

export function PlotlyInfoCard() {
  // Reading the same input ids that PlotlyCard sets — the value we display is
  // the local React state held by useShinyInput, not a server roundtrip.
  // (The values are also shipped to Shiny so the server can react to them
  // if it wants — see input.plotly_hover() etc. in app.py.)
  const [hover] = useShinyInput("plotly_hover", null);
  const [click] = useShinyInput("plotly_click", null, {
    debounceMs: 0,
    priority: "event",
  });
  const [ranges] = useShinyInput("plotly_xy_ranges", null);
  const [selection] = useShinyInput("plotly_selection", null);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Plotly Interaction</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <Row label="Hover" value={fmtPair(hover)} />
        <Row label="Click" value={fmtPair(click)} />
        <Row label="Visible range" value={fmtRange(ranges)} />
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
            Selection
          </p>
          {selection?.length ? (
            <div className="flex flex-wrap gap-1">
              {selection.map((p, i) => (
                <Badge key={i} variant="secondary">
                  {fmtPair(p)}
                </Badge>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">
              Drag to box-select points on the chart
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function Row({ label, value }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
        {label}
      </p>
      <pre className="bg-muted px-3 py-2 rounded-md text-xs overflow-x-auto">
        {value}
      </pre>
    </div>
  );
}
