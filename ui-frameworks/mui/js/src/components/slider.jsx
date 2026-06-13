import Slider from "@mui/material/Slider";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as a number.
function ShinySlider({ element }) {
  const {
    input_id,
    min = 0,
    max = 100,
    step = 1,
    value: dflt = 50,
    className,
  } = element.props;
  const [value, setValue] = useShinyInput(input_id, dflt);
  return (
    <Slider
      min={min}
      max={max}
      step={step}
      value={typeof value === "number" ? value : dflt}
      onChange={(_, v) => setValue(v)}
      valueLabelDisplay="auto"
      className={className}
    />
  );
}

export { ShinySlider as Slider };
