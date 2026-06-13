import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as the selected option.
function ShinyAutocomplete({ element }) {
  const { input_id, options, label, className } = element.props;
  const [value, setValue] = useShinyInput(input_id, null);
  return (
    <Autocomplete
      options={options}
      value={value ?? null}
      onChange={(_, v) => setValue(v)}
      renderInput={(params) => <TextField {...params} label={label} />}
      className={className}
    />
  );
}

export { ShinyAutocomplete as Autocomplete };
