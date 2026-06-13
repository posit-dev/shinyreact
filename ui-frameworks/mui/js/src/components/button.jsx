import Button from "@mui/material/Button";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Action: server reads input.<input_id>() as a click counter.
function ShinyButton({ element }) {
  const {
    input_id,
    label = "Button",
    variant = "contained",
    color = "primary",
    className,
  } = element.props;
  const [count, setCount] = useShinyInput(input_id, 0, {
    debounceMs: 0,
    priority: "event",
  });
  return (
    <Button
      variant={variant}
      color={color}
      className={className}
      onClick={() => setCount(count + 1)}
    >
      {label}
    </Button>
  );
}

export { ShinyButton as Button };
