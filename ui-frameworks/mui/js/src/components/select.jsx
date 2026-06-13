import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as the selected value string.
// `choices` is an array of strings, or {value, label} objects.
function ShinySelect({ element }) {
  const { input_id, label, choices = [], selected, className } = element.props;
  const opts = choices.map((c) =>
    typeof c === "string" ? { value: c, label: c } : c,
  );
  const [value, setValue] = useShinyInput(input_id, selected ?? opts[0]?.value ?? "");
  const labelId = `${input_id}-label`;
  return (
    <FormControl fullWidth className={className}>
      {label && <InputLabel id={labelId}>{label}</InputLabel>}
      <Select
        labelId={labelId}
        label={label}
        value={value ?? ""}
        onChange={(e) => setValue(e.target.value)}
      >
        {opts.map((o) => (
          <MenuItem key={o.value} value={o.value}>
            {o.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

export { ShinySelect as Select };
