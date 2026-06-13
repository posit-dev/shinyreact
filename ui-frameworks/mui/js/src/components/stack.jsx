import Stack from "@mui/material/Stack";

// --- shinyreact bridge ---
// Container: MUI Stack laying out children along one axis.
function ShinyStack({ element, children }) {
  const { direction = "column", spacing = 2, className } = element.props;
  return (
    <Stack direction={direction} spacing={spacing} className={className}>
      {children}
    </Stack>
  );
}

export { ShinyStack as Stack };
