import Fab from "@mui/material/Fab";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Action: server reads input.<input_id>() as a click counter.
function ShinyFab({ element }) {
  const {
    input_id,
    label,
    color = "primary",
    variant = "circular",
    className,
  } = element.props;
  const [count, setCount] = useShinyInput(input_id, 0, {
    debounceMs: 0,
    priority: "event",
  });
  return (
    <Fab
      color={color}
      variant={variant}
      className={className}
      onClick={() => setCount(count + 1)}
    >
      {label}
    </Fab>
  );
}

export { ShinyFab as Fab };
