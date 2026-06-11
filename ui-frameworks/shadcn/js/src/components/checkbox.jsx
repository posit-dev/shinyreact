import * as React from "react";
import { CheckIcon } from "lucide-react";
import { Checkbox as CheckboxPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";
import { useShinyInput } from "@/hooks";

// --- shadcn source (converted from TS) ---

function Checkbox({ className, ...props }) {
  return (
    <CheckboxPrimitive.Root
      data-slot="checkbox"
      className={cn(
        "peer size-4 shrink-0 rounded-[4px] border border-input shadow-xs transition-shadow outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:border-primary data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground",
        className
      )}
      {...props}
    >
      <CheckboxPrimitive.Indicator
        data-slot="checkbox-indicator"
        className="grid place-content-center text-current transition-none"
      >
        <CheckIcon className="size-3.5" />
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  );
}

// --- shinyreact bridge ---
// Props: input_id (str), label (str, optional), checked (bool, default false).
// Server reads input.<input_id>() as boolean.

function ShinyCheckbox({ element }) {
  const { input_id, label, checked: defaultChecked = false, className } = element.props;
  const [checked, setChecked] = useShinyInput(input_id, defaultChecked);
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Checkbox
        id={input_id}
        checked={!!checked}
        onCheckedChange={setChecked}
      />
      {label && (
        <label htmlFor={input_id} className="text-sm font-medium cursor-pointer">
          {label}
        </label>
      )}
    </div>
  );
}

export { ShinyCheckbox as Checkbox };
