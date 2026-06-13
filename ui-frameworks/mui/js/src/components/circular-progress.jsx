import CircularProgress from "@mui/material/CircularProgress";

// --- shinyreact bridge ---
// Display: value == null renders an indeterminate spinner; otherwise determinate.
function ShinyCircularProgress({ element }) {
  const { value, color = "primary", className } = element.props;
  return (
    <CircularProgress
      variant={value == null ? "indeterminate" : "determinate"}
      value={value ?? undefined}
      color={color}
      className={className}
    />
  );
}

export { ShinyCircularProgress as CircularProgress };
