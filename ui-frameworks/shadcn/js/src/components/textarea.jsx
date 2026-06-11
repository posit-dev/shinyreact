import * as React from "react";
import { cn } from "@/lib/utils";
import { useShinyInput } from "shinyreact";

// --- shadcn source (converted from TS) ---

function Textarea({ className, ...props }) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex field-sizing-content min-h-16 w-full rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-xs transition-[color,box-shadow] outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className
      )}
      {...props}
    />
  );
}

// --- shinyreact bridge ---
// Multi-line text input. Server reads input.<input_id>() as the current string.
// Props: input_id (str), placeholder (str), label (str, opt), debounce_ms (num),
//   className (str, opt — merged onto the wrapper).

function ShinyTextarea({ element }) {
  const { input_id, placeholder = "", label, debounce_ms = 250, className } = element.props;
  const [value, setValue] = useShinyInput(input_id, "", { debounceMs: debounce_ms });
  return (
    <div className={cn("flex flex-col gap-1.5 w-full", className)}>
      {label && <label className="text-sm font-medium">{label}</label>}
      <Textarea
        value={value}
        placeholder={placeholder}
        onChange={(e) => setValue(e.target.value)}
      />
    </div>
  );
}

export { ShinyTextarea as Textarea };
