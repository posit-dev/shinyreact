import * as React from "react";
import { Label as LabelPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";

// --- shadcn source (converted from TS) ---

function Label({ className, ...props }) {
  return (
    <LabelPrimitive.Root
      data-slot="label"
      className={cn(
        "flex items-center gap-2 text-sm leading-none font-medium select-none peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}

// --- shinyreact bridge ---
// Display-only text label. Props: text (str), className (str, optional).

function ShinyLabel({ element, children }) {
  const { text, className } = element.props;
  return <Label className={className}>{text ?? children}</Label>;
}

export { ShinyLabel as Label };
