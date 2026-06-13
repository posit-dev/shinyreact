import Button from "@mui/material/Button";
import Drawer from "@mui/material/Drawer";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Overlay: server reads input.<input_id>() as the boolean open state.
function ShinyDrawer({ element, children }) {
  const {
    input_id,
    trigger_label = "Open",
    anchor = "left",
    className,
  } = element.props;
  const [open, setOpen] = useShinyInput(input_id, false);
  return (
    <>
      <Button variant="outlined" onClick={() => setOpen(true)}>
        {trigger_label}
      </Button>
      <Drawer
        anchor={anchor}
        open={!!open}
        onClose={() => setOpen(false)}
        className={className}
      >
        {children}
      </Drawer>
    </>
  );
}

export { ShinyDrawer as Drawer };
