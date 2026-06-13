import Alert from "@mui/material/Alert";

// --- shinyreact bridge ---
// Display: a status message. severity = error | warning | info | success.
function ShinyAlert({ element }) {
  const { text, severity = "info", variant = "standard", className } = element.props;
  return (
    <Alert severity={severity} variant={variant} className={className}>
      {text}
    </Alert>
  );
}

export { ShinyAlert as Alert };
