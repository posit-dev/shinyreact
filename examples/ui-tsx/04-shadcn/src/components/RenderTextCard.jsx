import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const { useShinyOutputValue, useShinyOutputStatus } = window.shinyreact;

export function RenderTextCard() {
  const value = useShinyOutputValue("render_text_demo", "");
  const status = useShinyOutputStatus("render_text_demo");
  const recalculating = status === "recalculating";

  return (
    <Card>
      <CardHeader>
        <CardTitle>shiny.render.text</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-sm text-muted-foreground">
          This card consumes a plain <code>@render.text</code> output (no{" "}
          <code>reactive_output</code>) via <code>useShinyOutputValue</code>.
        </p>
        <div className="bg-muted p-3 rounded-md">
          <pre className="text-sm whitespace-pre-wrap">
            {recalculating ? "…" : value || "(empty — type in the box above)"}
          </pre>
        </div>
      </CardContent>
    </Card>
  );
}
