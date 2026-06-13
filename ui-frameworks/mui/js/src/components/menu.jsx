import Button from "@mui/material/Button";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import * as React from "react";
import { useSetShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Collection: server reads input.<input_id>() as the picked {value, nonce}.
function ShinyMenu({ element }) {
  const { input_id, trigger_label = "Open", items = [], className } = element.props;
  const [anchorEl, setAnchorEl] = React.useState(null);
  const setSelected = useSetShinyInput(input_id, null, {
    debounceMs: 0,
    priority: "event",
  });
  const onPick = (v) => {
    setSelected({ value: v, nonce: Date.now() });
    setAnchorEl(null);
  };
  return (
    <>
      <Button onClick={(e) => setAnchorEl(e.currentTarget)}>{trigger_label}</Button>
      <Menu
        anchorEl={anchorEl}
        open={!!anchorEl}
        onClose={() => setAnchorEl(null)}
        className={className}
      >
        {items.map((it) => (
          <MenuItem key={it.value} onClick={() => onPick(it.value)}>
            {it.label}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}

export { ShinyMenu as Menu };
