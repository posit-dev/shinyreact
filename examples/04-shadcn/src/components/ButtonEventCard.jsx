import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const { useShinyInput, useShinyOutputValue } = window.shinyreact;

export function ButtonEventCard() {
  const [buttonTrigger, setButtonTrigger] = useShinyInput("button_trigger", 0, {
    debounceMs: 0,
    priority: "event",
  });
  const buttonResponse = useShinyOutputValue("button_response", "");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Button Events</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm text-muted-foreground mb-2">
            Click to trigger server event:
          </p>
          <Button
            onClick={() => setButtonTrigger(buttonTrigger + 1)}
            variant="default"
            className="w-full"
          >
            Send Event
          </Button>
        </div>
        <div>
          <p className="text-sm text-muted-foreground mb-2">Server response:</p>
          <div className="bg-muted p-3 rounded-md">
            <pre className="text-sm">
              {buttonResponse || "Click button to see response"}
            </pre>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
