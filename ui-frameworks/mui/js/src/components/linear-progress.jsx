import LinearProgress from "@mui/material/LinearProgress";

// --- shinyreact bridge ---
// Display: value == null renders an indeterminate bar; otherwise determinate.
function ShinyLinearProgress({ element }) {
  const { value, color = "primary", className } = element.props;
  return (
    <LinearProgress
      variant={value == null ? "indeterminate" : "determinate"}
      value={value ?? undefined}
      color={color}
      className={className}
    />
  );
}

export { ShinyLinearProgress as LinearProgress };
