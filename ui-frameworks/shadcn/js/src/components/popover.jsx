import * as React from "react";
import { Popover as PopoverPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";
import { TriggerButton } from "@/lib/trigger-button";
import { useShinyInput } from "@/hooks";

// --- shadcn source (converted from TS) ---

function Popover({ ...props }) {
  return <PopoverPrimitive.Root data-slot="popover" {...props} />;
}

function PopoverTrigger({ ...props }) {
  return <PopoverPrimitive.Trigger data-slot="popover-trigger" {...props} />;
}

function PopoverContent({ className, align = "center", sideOffset = 4, ...props }) {
  return (
    <PopoverPrimitive.Portal>
      <PopoverPrimitive.Content
        data-slot="popover-content"
        align={align}
        sideOffset={sideOffset}
        className={cn(
          "z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
          className
        )}
        {...props}
      />
    </PopoverPrimitive.Portal>
  );
}

// --- shinyreact bridge ---
// Props: input_id (str), trigger_label (str, default "Open"),
//   align ("start" | "center" | "end", default "center").
// Children: popover body content from the node tree.
// Server reads input.<input_id>() as boolean — true while popover is open.

function ShinyPopover({ element, children }) {
  const { input_id, trigger_label = "Open", align = "center", className } = element.props;
  const [open, setOpen] = useShinyInput(input_id, false);
  return (
    <Popover open={!!open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <TriggerButton>{trigger_label}</TriggerButton>
      </PopoverTrigger>
      <PopoverContent align={align} className={className}>
        <div className="flex flex-col gap-3">{children}</div>
      </PopoverContent>
    </Popover>
  );
}

export { ShinyPopover as Popover };
