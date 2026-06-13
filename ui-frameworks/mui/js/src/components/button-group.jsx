import ButtonGroup from "@mui/material/ButtonGroup";

// --- shinyreact bridge ---
// Container: groups child buttons.
function ShinyButtonGroup({ element, children }) {
  const {
    variant = "contained",
    orientation = "horizontal",
    color = "primary",
    className,
  } = element.props;
  return (
    <ButtonGroup
      variant={variant}
      orientation={orientation}
      color={color}
      className={className}
    >
      {children}
    </ButtonGroup>
  );
}

export { ShinyButtonGroup as ButtonGroup };
