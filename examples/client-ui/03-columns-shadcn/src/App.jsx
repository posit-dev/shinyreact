import { ArrowLeft, ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const { useShinyInput, useShinyOutput, useShinyInitialized } = window.shinyreact;

const COLUMNS = ["A", "B", "C"];

function ItemRow({ item, colIdx, onMove }) {
  return (
    <div className="flex items-center gap-2 rounded-md border bg-background px-3 py-2">
      <span className="flex-1 text-sm">{item}</span>
      {colIdx > 0 && (
        <Button
          variant="outline"
          size="icon"
          aria-label="Move left"
          onClick={() => onMove(item, COLUMNS[colIdx], COLUMNS[colIdx - 1])}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
      )}
      {colIdx < COLUMNS.length - 1 && (
        <Button
          variant="outline"
          size="icon"
          aria-label="Move right"
          onClick={() => onMove(item, COLUMNS[colIdx], COLUMNS[colIdx + 1])}
        >
          <ArrowRight className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}

function Column({ name, colIdx, items, onMove }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Column {name}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {items && items.length > 0 ? (
          items.map((item) => (
            <ItemRow key={item} item={item} colIdx={colIdx} onMove={onMove} />
          ))
        ) : (
          <p className="text-sm text-muted-foreground">(empty)</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function App() {
  const initialized = useShinyInitialized();
  const [, setMoveItem] = useShinyInput("move_item", null, {
    debounceMs: 0,
    priority: "event",
  });
  const [data] = useShinyOutput("column_data", null);

  if (!initialized) return null;

  function handleMove(item, fromCol, toCol) {
    setMoveItem({ item, from: fromCol, to: toCol });
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <h1 className="mb-1 text-2xl font-semibold tracking-tight">
        Move Items Between Columns
      </h1>
      <p className="mb-6 text-sm text-muted-foreground">
        client-ui-first Shiny app rendered with shadcn/ui components.
      </p>
      <div className="grid grid-cols-3 gap-4">
        {COLUMNS.map((col, colIdx) => (
          <Column
            key={col}
            name={col}
            colIdx={colIdx}
            items={data ? data[col] : null}
            onMove={handleMove}
          />
        ))}
      </div>
    </div>
  );
}
