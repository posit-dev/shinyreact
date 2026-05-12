import { Slider as MuiSlider, Typography, Box } from "@mui/material";
import type { RegisteredComponentProps } from "../types";

const { useShinyInput } = window.shinyreact;

export function Slider({ element }: RegisteredComponentProps) {
  const {
    input_id,
    label,
    default_value,
    min,
    max,
    step,
    debounce_ms,
  } = element.props as {
    input_id: string;
    label?: string;
    default_value?: number;
    min?: number;
    max?: number;
    step?: number;
    debounce_ms?: number;
  };

  const [value, setValue] = useShinyInput<number>(input_id, default_value ?? 0, {
    debounceMs: debounce_ms ?? 100,
  });

  return (
    <Box>
      {label && <Typography gutterBottom>{label}: {value}</Typography>}
      <MuiSlider
        value={value ?? 0}
        onChange={(_, v) => setValue(typeof v === "number" ? v : v[0])}
        min={min ?? 0}
        max={max ?? 100}
        step={step ?? 1}
        valueLabelDisplay="auto"
      />
    </Box>
  );
}
