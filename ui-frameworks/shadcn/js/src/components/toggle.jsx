import { cva } from "class-variance-authority";
import { Toggle as TogglePrimitive } from "radix-ui";
import { cn } from "@/lib/utils";
import { useShinyInput } from "@/hooks";

const toggleVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium whitespace-nowrap transition-[color,box-shadow] outline-none hover:bg-muted hover:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-destructive/20 data-[state=on]:bg-accent data-[state=on]:text-accent-foreground dark:aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-transparent",
        outline: "border border-input bg-transparent shadow-xs hover:bg-accent hover:text-accent-foreground"
      },
      size: {
        default: "h-9 min-w-9 px-2",
        sm: "h-8 min-w-8 px-1.5",
        lg: "h-10 min-w-10 px-2.5"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
);
function Toggle({
  className,
  variant,
  size,
  ...props
}) {
  return <TogglePrimitive.Root
    data-slot="toggle"
    className={cn(toggleVariants({ variant, size, className }))}
    {...props}
  />;
}

// --- shinyreact bridge ---
// A two-state toggle button. Server reads input.<input_id>() as a boolean.
// Props: input_id (str), label (str), pressed (bool, default false),
//   variant ("default" | "outline"), size ("default" | "sm" | "lg"), className.

function ShinyToggle({ element }) {
  const {
    input_id,
    label,
    pressed: defaultPressed = false,
    variant = "default",
    size = "default",
    className,
  } = element.props;
  const [pressed, setPressed] = useShinyInput(input_id, defaultPressed);
  return (
    <Toggle
      pressed={!!pressed}
      onPressedChange={setPressed}
      variant={variant}
      size={size}
      aria-label={label}
      className={className}
    >
      {label}
    </Toggle>
  );
}

// toggleVariants is re-exported so toggle-group can share the cva (shadcn does this).
export { ShinyToggle as Toggle, toggleVariants };
