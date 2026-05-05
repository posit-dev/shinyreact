import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const { useShinyInput, useShinyOutput } = window.shinyjson;

export function TextInputCard() {
  const [inputText, setInputText] = useShinyInput("user_text", "");
  const [processedText] = useShinyOutput("processed_text", "");
  const [textLength] = useShinyOutput("text_length", 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Text Input</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label
            htmlFor="text-input"
            className="text-sm font-medium mb-2 block"
          >
            Enter some text:
          </label>
          <Input
            id="text-input"
            type="text"
            placeholder="Type something..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
        </div>
        <div>
          <p className="text-sm text-muted-foreground mb-2">
            Processed text from server:
          </p>
          <div className="bg-muted p-3 rounded-md">
            <pre className="text-sm">
              {processedText || "No text entered yet"}
            </pre>
          </div>
        </div>
        <div className="text-sm">
          <Badge variant="secondary">Length: {textLength}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
