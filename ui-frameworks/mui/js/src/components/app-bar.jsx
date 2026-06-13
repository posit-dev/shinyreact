import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";

// --- shinyreact bridge ---
// Container: top app bar with an optional title and trailing children.
function ShinyAppBar({ element, children }) {
  const { title, position = "static", className } = element.props;
  return (
    <AppBar position={position} className={className}>
      <Toolbar>
        {title && (
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {title}
          </Typography>
        )}
        {children}
      </Toolbar>
    </AppBar>
  );
}

export { ShinyAppBar as AppBar };
