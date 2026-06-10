import { useShinyInput } from "@/hooks";

const variants = {
  default: "bg-primary text-primary-foreground hover:bg-primary/90",
  outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
  secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
  ghost: "hover:bg-accent hover:text-accent-foreground",
};

export function Button({ element }) {
  const { input_id, label, variant = "default" } = element.props;
  const [count, setCount] = useShinyInput(input_id, 0, { debounceMs: 0, priority: "event" });
  return (
    <button
      className={`inline-flex w-full items-center justify-center rounded-md text-sm font-medium h-9 px-4 py-2 shadow transition-colors cursor-pointer ${variants[variant] ?? variants.default}`}
      onClick={() => setCount(count + 1)}
    >
      {label}
    </button>
  );
}
