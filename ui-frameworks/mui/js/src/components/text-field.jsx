import TextField from "@mui/material/TextField";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as the current string.
function ShinyTextField({ element }) {
  const {
    input_id,
    label,
    placeholder,
    variant = "outlined",
    debounce_ms = 250,
    className,
  } = element.props;
  const [value, setValue] = useShinyInput(input_id, "", { debounceMs: debounce_ms });
  return (
    <TextField
      label={label}
      placeholder={placeholder}
      variant={variant}
      value={value ?? ""}
      onChange={(e) => setValue(e.target.value)}
      className={className}
    />
  );
}

export { ShinyTextField as TextField };
