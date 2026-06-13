import Backdrop from "@mui/material/Backdrop";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Overlay: server reads input.<input_id>() as the boolean open state.
function ShinyBackdrop({ element, children }) {
  const { input_id, className } = element.props;
  const [open, setOpen] = useShinyInput(input_id, false);
  return (
    <Backdrop open={!!open} onClick={() => setOpen(false)} className={className}>
      {children}
    </Backdrop>
  );
}

export { ShinyBackdrop as Backdrop };
