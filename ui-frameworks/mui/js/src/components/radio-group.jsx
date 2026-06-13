import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormLabel from "@mui/material/FormLabel";
import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as the selected value.
function ShinyRadioGroup({ element }) {
  const { input_id, choices, label, selected, className } = element.props;
  const opts = choices.map((c) =>
    typeof c === "string" ? { value: c, label: c } : c,
  );
  const [value, setValue] = useShinyInput(
    input_id,
    selected ?? opts[0]?.value ?? "",
  );
  return (
    <FormControl className={className}>
      {label && <FormLabel>{label}</FormLabel>}
      <RadioGroup
        value={value ?? ""}
        onChange={(e) => setValue(e.target.value)}
      >
        {opts.map((o) => (
          <FormControlLabel
            key={o.value}
            value={o.value}
            control={<Radio />}
            label={o.label}
          />
        ))}
      </RadioGroup>
    </FormControl>
  );
}

export { ShinyRadioGroup as RadioGroup };
