import Snackbar from "@mui/material/Snackbar";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Overlay: server reads input.<input_id>() as the boolean open state.
function ShinySnackbar({ element }) {
  const { input_id, message, auto_hide_ms = 4000, className } = element.props;
  const [open, setOpen] = useShinyInput(input_id, false);
  return (
    <Snackbar
      open={!!open}
      autoHideDuration={auto_hide_ms}
      onClose={() => setOpen(false)}
      message={message}
      className={className}
    />
  );
}

export { ShinySnackbar as Snackbar };
