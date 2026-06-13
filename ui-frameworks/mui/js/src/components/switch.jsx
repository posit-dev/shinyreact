import FormControlLabel from "@mui/material/FormControlLabel";
import Switch from "@mui/material/Switch";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as a boolean.
function ShinySwitch({ element }) {
  const { input_id, label, className } = element.props;
  const [checked, setChecked] = useShinyInput(input_id, false);
  const control = (
    <Switch
      checked={!!checked}
      onChange={(e) => setChecked(e.target.checked)}
      className={className}
    />
  );
  return label ? <FormControlLabel control={control} label={label} /> : control;
}

export { ShinySwitch as Switch };
