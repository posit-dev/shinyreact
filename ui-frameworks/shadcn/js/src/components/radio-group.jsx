import { CircleIcon } from "lucide-react";
import { RadioGroup as RadioGroupPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";
import { useShinyInput } from "@/hooks";
function RadioGroup({
  className,
  ...props
}) {
  return <RadioGroupPrimitive.Root
    data-slot="radio-group"
    className={cn("grid gap-3", className)}
    {...props}
  />;
}
function RadioGroupItem({
  className,
  ...props
}) {
  return <RadioGroupPrimitive.Item
    data-slot="radio-group-item"
    className={cn(
      "aspect-square size-4 shrink-0 rounded-full border border-input text-primary shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:bg-input/30 dark:aria-invalid:ring-destructive/40",
      className
    )}
    {...props}
  ><RadioGroupPrimitive.Indicator
    data-slot="radio-group-indicator"
    className="relative flex items-center justify-center"
  ><CircleIcon className="absolute top-1/2 left-1/2 size-2 -translate-x-1/2 -translate-y-1/2 fill-primary" /></RadioGroupPrimitive.Indicator></RadioGroupPrimitive.Item>;
}

// --- shinyreact bridge ---
// Single-select radio group. Server reads input.<input_id>() as the value.
// Props: input_id (str), choices (str[] | {value,label}[]), selected (str, opt),
//   label (str, opt), className (opt).

function ShinyRadioGroup({ element }) {
  const { input_id, choices = [], selected, label, className } = element.props;
  const first = choices.length
    ? typeof choices[0] === "object"
      ? choices[0].value
      : choices[0]
    : "";
  const [value, setValue] = useShinyInput(input_id, selected ?? first);
  return (
    <div className={cn("flex flex-col gap-3", className)}>
      {label && <label className="text-sm font-medium">{label}</label>}
      <RadioGroup value={value} onValueChange={setValue}>
        {choices.map((c) => {
          const val = typeof c === "object" ? c.value : c;
          const lbl = typeof c === "object" ? c.label : c;
          return (
            <div key={val} className="flex items-center gap-2">
              <RadioGroupItem value={val} id={`${input_id}-${val}`} />
              <label htmlFor={`${input_id}-${val}`} className="text-sm">
                {lbl}
              </label>
            </div>
          );
        })}
      </RadioGroup>
    </div>
  );
}

export { ShinyRadioGroup as RadioGroup };
