import * as React from "react";
import { Switch as SwitchPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";
import { useShinyInput } from "@/hooks";

// --- shadcn source (converted from TS) ---

function Switch({ className, size = "default", ...props }) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      data-size={size}
      className={cn(
        "peer group/switch inline-flex shrink-0 items-center rounded-full border border-transparent shadow-xs transition-all outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 data-[size=default]:h-[1.15rem] data-[size=default]:w-8 data-[size=sm]:h-3.5 data-[size=sm]:w-6 data-[state=checked]:bg-primary data-[state=unchecked]:bg-input",
        className
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        data-slot="switch-thumb"
        className="pointer-events-none block rounded-full bg-background ring-0 transition-transform group-data-[size=default]/switch:size-4 group-data-[size=sm]/switch:size-3 data-[state=checked]:translate-x-[calc(100%-2px)] data-[state=unchecked]:translate-x-0"
      />
    </SwitchPrimitive.Root>
  );
}

// --- shinyreact bridge ---
// Props: input_id (str), label (str, optional), checked (bool, default false).
// Server reads input.<input_id>() as boolean.

function ShinySwitch({ element }) {
  const { input_id, label, checked: defaultChecked = false, className } = element.props;
  const [checked, setChecked] = useShinyInput(input_id, defaultChecked);
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <Switch checked={!!checked} onCheckedChange={setChecked} />
      {label && <label className="text-sm font-medium">{label}</label>}
    </div>
  );
}

export { ShinySwitch as Switch };
