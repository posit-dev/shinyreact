import Typography from "@mui/material/Typography";

// --- shinyreact bridge ---
// Display: text rendered with an MUI typography variant.
function ShinyTypography({ element }) {
  const { text, variant = "body1", align, color, className } = element.props;
  // Coerce null/None -> undefined so MUI uses its defaults. Passing align={null}
  // makes MUI call capitalize(null) (it only skips when align === "inherit"),
  // which throws "capitalize expects a string" (MUI error #7).
  return (
    <Typography
      variant={variant}
      align={align ?? undefined}
      color={color ?? undefined}
      className={className}
    >
      {text}
    </Typography>
  );
}

export { ShinyTypography as Typography };
