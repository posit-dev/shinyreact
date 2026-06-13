import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as the selected value(s).
function ShinyToggleButtonGroup({ element }) {
  const { input_id, choices, exclusive = true, className } = element.props;
  const opts = choices.map((c) =>
    typeof c === "string" ? { value: c, label: c } : c,
  );
  const [value, setValue] = useShinyInput(input_id, null);
  return (
    <ToggleButtonGroup
      value={value}
      exclusive={!!exclusive}
      onChange={(_, v) => setValue(v)}
      className={className}
    >
      {opts.map((o) => (
        <ToggleButton key={o.value} value={o.value}>
          {o.label}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}

export { ShinyToggleButtonGroup as ToggleButtonGroup };
