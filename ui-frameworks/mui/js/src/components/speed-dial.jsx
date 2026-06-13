import SpeedDial from "@mui/material/SpeedDial";
import SpeedDialAction from "@mui/material/SpeedDialAction";
import { useSetShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Collection: server reads input.<input_id>() as the picked {value, nonce}.
function ShinySpeedDial({ element }) {
  const { input_id, actions = [], className } = element.props;
  const setSelected = useSetShinyInput(input_id, null, {
    debounceMs: 0,
    priority: "event",
  });
  return (
    <SpeedDial ariaLabel="speed-dial" icon={<span>+</span>} className={className}>
      {actions.map((a) => (
        <SpeedDialAction
          key={a.value}
          icon={<span>{(a.label || "•")[0]}</span>}
          tooltipTitle={a.label}
          onClick={() => setSelected({ value: a.value, nonce: Date.now() })}
        />
      ))}
    </SpeedDial>
  );
}

export { ShinySpeedDial as SpeedDial };
