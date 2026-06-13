import Grid from "@mui/material/Grid";

// --- shinyreact bridge ---
// Container: MUI Grid in container mode.
function ShinyGrid({ element, children }) {
  const { spacing = 2, className } = element.props;
  return (
    <Grid container spacing={spacing} className={className}>
      {children}
    </Grid>
  );
}

export { ShinyGrid as Grid };
