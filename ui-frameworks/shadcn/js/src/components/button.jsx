import { Button as ButtonBase } from "@/lib/button-base";
import { useShinyInput } from "@/hooks";

// --- shinyreact bridge ---
// Action button. Server reads input.<input_id>() as a click counter.
// Props: input_id (str), label (str), variant (str, default "default").

function ShinyButton({ element }) {
  const { input_id, label, variant = "default" } = element.props;
  const [count, setCount] = useShinyInput(input_id, 0, { debounceMs: 0, priority: "event" });
  return (
    <ButtonBase
      variant={variant}
      className="w-full cursor-pointer"
      onClick={() => setCount(count + 1)}
    >
      {label}
    </ButtonBase>
  );
}

export { ShinyButton as Button };
