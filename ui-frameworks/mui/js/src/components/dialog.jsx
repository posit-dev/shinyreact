import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Overlay: server reads input.<input_id>() as the boolean open state.
// MUI's Dialog renders through a portal (why react-dom is bundled, not externalized).
function ShinyDialog({ element, children }) {
  const { input_id, trigger_label = "Open", title, className } = element.props;
  const [open, setOpen] = useShinyInput(input_id, false);
  return (
    <>
      <Button variant="outlined" onClick={() => setOpen(true)}>
        {trigger_label}
      </Button>
      <Dialog open={!!open} onClose={() => setOpen(false)} className={className}>
        {title && <DialogTitle>{title}</DialogTitle>}
        <DialogContent>{children}</DialogContent>
      </Dialog>
    </>
  );
}

export { ShinyDialog as Dialog };
