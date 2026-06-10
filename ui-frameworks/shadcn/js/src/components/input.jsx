import { useShinyInput } from "@/hooks";

export function Input({ element }) {
  const { input_id, placeholder = "", label, debounce_ms = 250 } = element.props;
  const [value, setValue] = useShinyInput(input_id, "", { debounceMs: debounce_ms });
  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && <label className="text-sm font-medium">{label}</label>}
      <input
        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        value={value}
        placeholder={placeholder}
        onChange={(e) => setValue(e.target.value)}
      />
    </div>
  );
}
