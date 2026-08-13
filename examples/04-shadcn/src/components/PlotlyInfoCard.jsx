import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const { useShinyInputValue } = window.shinyreact;

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
  // Read the input ids that PlotlyCard writes via useShinyInput. This card is
  // a pure consumer — it never sets these values — so useShinyInputValue is
  // the right hook: read-only, no setter. Updates flow through the local React
  // state held by the input registry, not a server roundtrip. (The values are
  // also shipped to Shiny so the server can react to them if it wants — see
  // input.plotly_hover() etc. in app.py.)
  const hover = useShinyInputValue("plotly_hover");
  const click = useShinyInputValue("plotly_click");
  const dblclick = useShinyInputValue("plotly_dblclick");
  const ranges = useShinyInputValue("plotly_xy_ranges");
  const selection = useShinyInputValue("plotly_selection");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Plotly Interaction</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <Row label="Hover" value={fmtPair(hover)} />
        <Row label="Click" value={fmtPair(click)} />
        <Row label="Double-click" value={fmtPair(dblclick)} />
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
