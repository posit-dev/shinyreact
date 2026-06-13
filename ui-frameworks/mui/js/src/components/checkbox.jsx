import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as a boolean.
function ShinyCheckbox({ element }) {
  const { input_id, label, className } = element.props;
  const [checked, setChecked] = useShinyInput(input_id, false);
  const control = (
    <Checkbox
      checked={!!checked}
      onChange={(e) => setChecked(e.target.checked)}
      className={className}
    />
  );
  return label ? <FormControlLabel control={control} label={label} /> : control;
}

export { ShinyCheckbox as Checkbox };
