import Box from "@mui/material/Box";

// --- shinyreact bridge ---
// Container: wraps children in an MUI Box.
function ShinyBox({ element, children }) {
  const { className } = element.props;
  return <Box className={className}>{children}</Box>;
}

export { ShinyBox as Box };
