import * as React from "react";
import { ToggleGroup as ToggleGroupPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";
import { toggleVariants } from "@/components/toggle";
import { useShinyInput } from "@/hooks";
const ToggleGroupContext = React.createContext({
  size: "default",
  variant: "default",
  spacing: 0
});
function ToggleGroup({
  className,
  variant,
  size,
  spacing = 0,
  children,
  ...props
}) {
  return <ToggleGroupPrimitive.Root
    data-slot="toggle-group"
    data-variant={variant}
    data-size={size}
    data-spacing={spacing}
    style={{ "--gap": spacing }}
    className={cn(
      "group/toggle-group flex w-fit items-center gap-[--spacing(var(--gap))] rounded-md data-[spacing=default]:data-[variant=outline]:shadow-xs",
      className
    )}
    {...props}
  ><ToggleGroupContext.Provider value={{ variant, size, spacing }}>{children}</ToggleGroupContext.Provider></ToggleGroupPrimitive.Root>;
}
function ToggleGroupItem({
  className,
  children,
  variant,
  size,
  ...props
}) {
  const context = React.useContext(ToggleGroupContext);
  return <ToggleGroupPrimitive.Item
    data-slot="toggle-group-item"
    data-variant={context.variant || variant}
    data-size={context.size || size}
    data-spacing={context.spacing}
    className={cn(
      toggleVariants({
        variant: context.variant || variant,
        size: context.size || size
      }),
      "w-auto min-w-0 shrink-0 px-3 focus:z-10 focus-visible:z-10",
      "data-[spacing=0]:rounded-none data-[spacing=0]:shadow-none data-[spacing=0]:first:rounded-l-md data-[spacing=0]:last:rounded-r-md data-[spacing=0]:data-[variant=outline]:border-l-0 data-[spacing=0]:data-[variant=outline]:first:border-l",
      className
    )}
    {...props}
  >{children}</ToggleGroupPrimitive.Item>;
}

// --- shinyreact bridge ---
// A group of toggle buttons (single- or multi-select). Server reads
// input.<input_id>() as the selected value (string for "single", string[] for
// "multiple"). Props: input_id, choices (str[] | {value,label}[]), type
// ("single" | "multiple"), selected, variant, size, className.

function ShinyToggleGroup({ element }) {
  const {
    input_id,
    choices = [],
    type = "single",
    selected,
    variant = "outline",
    size = "default",
    className,
  } = element.props;
  const fallback = type === "multiple" ? [] : "";
  const [value, setValue] = useShinyInput(input_id, selected ?? fallback);
  return (
    <ToggleGroup
      type={type}
      value={value}
      onValueChange={setValue}
      variant={variant}
      size={size}
      className={className}
    >
      {choices.map((c) => {
        const val = typeof c === "object" ? c.value : c;
        const lbl = typeof c === "object" ? c.label : c;
        return (
          <ToggleGroupItem key={val} value={val} aria-label={lbl}>
            {lbl}
          </ToggleGroupItem>
        );
      })}
    </ToggleGroup>
  );
}

export { ShinyToggleGroup as ToggleGroup };
