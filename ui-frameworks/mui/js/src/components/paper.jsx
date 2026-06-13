import Paper from "@mui/material/Paper";

// --- shinyreact bridge ---
// Container: wraps children in an MUI Paper surface.
function ShinyPaper({ element, children }) {
  const { elevation = 1, className } = element.props;
  return (
    <Paper elevation={elevation} className={className}>
      {children}
    </Paper>
  );
}

export { ShinyPaper as Paper };
