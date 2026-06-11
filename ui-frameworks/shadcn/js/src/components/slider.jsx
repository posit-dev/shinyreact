import * as React from "react";
import { Slider as SliderPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";
import { useShinyInput } from "shinyreact";

// --- shadcn source (converted from TS) ---

function Slider({ className, defaultValue, value, min = 0, max = 100, ...props }) {
  const _values = React.useMemo(
    () => (Array.isArray(value) ? value : Array.isArray(defaultValue) ? defaultValue : [min]),
    [value, defaultValue, min]
  );
  return (
    <SliderPrimitive.Root
      data-slot="slider"
      defaultValue={defaultValue}
      value={value}
      min={min}
      max={max}
      className={cn(
        "relative flex w-full touch-none items-center select-none data-[disabled]:opacity-50",
        className
      )}
      {...props}
    >
      <SliderPrimitive.Track
        data-slot="slider-track"
        className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-muted"
      >
        <SliderPrimitive.Range
          data-slot="slider-range"
          className="absolute h-full bg-primary"
        />
      </SliderPrimitive.Track>
      {Array.from({ length: _values.length }, (_, i) => (
        <SliderPrimitive.Thumb
          key={i}
          data-slot="slider-thumb"
          className="block size-4 shrink-0 rounded-full border border-primary bg-white shadow-sm ring-ring/50 transition-[color,box-shadow] hover:ring-4 focus-visible:ring-4 focus-visible:outline-hidden disabled:pointer-events-none disabled:opacity-50"
        />
      ))}
    </SliderPrimitive.Root>
  );
}

// --- shinyreact bridge ---
// Props: input_id (str), min (num), max (num), step (num), value (num), label (str, optional).
// Server reads input.<input_id>() as a number.

function ShinySlider({ element }) {
  const { input_id, min = 0, max = 100, step = 1, value: defaultValue = 50, label, className } = element.props;
  const [value, setValue] = useShinyInput(input_id, defaultValue);
  return (
    <div className={cn("flex flex-col gap-2 w-full", className)}>
      {label && (
        <div className="flex justify-between items-center">
          <label className="text-sm font-medium">{label}</label>
          <span className="text-sm text-muted-foreground">{value}</span>
        </div>
      )}
      <Slider
        value={[value]}
        onValueChange={([v]) => setValue(v)}
        min={min}
        max={max}
        step={step}
      />
    </div>
  );
}

export { ShinySlider as Slider };
