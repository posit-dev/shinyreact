import type { RegisteredComponentProps } from "../types";

const { useShinyInput } = window.shinyreact;

export function {{Stub}}({ element }: RegisteredComponentProps) {
  const { label, input_id } = element.props as {
    label: string;
    input_id: string;
  };

  const [count, setCount] = useShinyInput<number>(input_id, 0, {
    debounceMs: 0,
    priority: "event",
  });

  return (
    <button onClick={() => setCount((count ?? 0) + 1)}>
      {label} (clicks: {count ?? 0})
    </button>
  );
}
