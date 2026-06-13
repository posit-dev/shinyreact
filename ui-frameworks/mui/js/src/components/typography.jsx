import Typography from "@mui/material/Typography";

// --- shinyreact bridge ---
// Display: text rendered with an MUI typography variant.
function ShinyTypography({ element }) {
  const { text, variant = "body1", align, color, className } = element.props;
  return (
    <Typography variant={variant} align={align} color={color} className={className}>
      {text}
    </Typography>
  );
}

export { ShinyTypography as Typography };
