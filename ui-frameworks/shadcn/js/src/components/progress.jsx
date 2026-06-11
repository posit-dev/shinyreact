import * as React from "react";
import { Progress as ProgressPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";

// --- shadcn source (converted from TS) ---

function Progress({ className, value, ...props }) {
  return (
    <ProgressPrimitive.Root
      data-slot="progress"
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-primary/20", className)}
      {...props}
    >
      <ProgressPrimitive.Indicator
        data-slot="progress-indicator"
        className="h-full w-full flex-1 bg-primary transition-all"
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </ProgressPrimitive.Root>
  );
}

// --- shinyreact bridge ---
// A determinate progress bar. Props: value (0–100), className (optional).
// Display-only; drive `value` from a reactive_output or render_react.

function ShinyProgress({ element }) {
  const { value = 0, className } = element.props;
  return <Progress value={value} className={className} />;
}

export { ShinyProgress as Progress };
