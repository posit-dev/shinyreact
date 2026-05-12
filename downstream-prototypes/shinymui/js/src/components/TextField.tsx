import { TextField as MuiTextField } from "@mui/material";
import type { RegisteredComponentProps } from "../types";

const { useShinyInput } = window.shinyreact;

export function TextField({ element }: RegisteredComponentProps) {
  const {
    input_id,
    label,
    default_value,
    placeholder,
    helper_text,
    debounce_ms,
  } = element.props as {
    input_id: string;
    label?: string;
    default_value?: string;
    placeholder?: string;
    helper_text?: string;
    debounce_ms?: number;
  };

  const [value, setValue] = useShinyInput<string>(input_id, default_value ?? "", {
    debounceMs: debounce_ms ?? 250,
  });

  return (
    <MuiTextField
      label={label}
      placeholder={placeholder}
      helperText={helper_text}
      value={value ?? ""}
      onChange={(e) => setValue(e.target.value)}
      fullWidth
    />
  );
}
