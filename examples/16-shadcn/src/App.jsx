import { ButtonEventCard } from "@/components/ButtonEventCard";
import { PlotCard } from "@/components/PlotCard";
import { PlotlyCard } from "@/components/PlotlyCard";
import { PlotlyInfoCard } from "@/components/PlotlyInfoCard";
import { TextInputCard } from "@/components/TextInputCard";
import { Separator } from "@/components/ui/separator";

const { useShinyInitialized } = window.shinyjson;

export default function App() {
  const initialized = useShinyInitialized();
  if (!initialized) return null;

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            Shiny + React + shadcn/ui
          </h1>
          <p className="text-muted-foreground mt-2">
            Demonstrating shadcn/ui components with various shinyjson output
            types
          </p>
        </div>

        <Separator />

        <div className="grid gap-6 md:grid-cols-2">
          <TextInputCard />
          <ButtonEventCard />
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <PlotCard />
          <PlotlyCard />
        </div>

        <div className="grid gap-6 md:grid-cols-1">
          <PlotlyInfoCard />
        </div>
      </div>
    </div>
  );
}
