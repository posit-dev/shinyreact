import Chip from "@mui/material/Chip";

// --- shinyreact bridge ---
// Display: a compact label/tag chip.
function ShinyChip({ element }) {
  const { label, color = "default", variant = "filled", className } = element.props;
  return (
    <Chip label={label} color={color} variant={variant} className={className} />
  );
}

export { ShinyChip as Chip };
