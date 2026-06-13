import Divider from "@mui/material/Divider";

// --- shinyreact bridge ---
// Display: a separator line, optionally with inline text.
function ShinyDivider({ element }) {
  const { orientation = "horizontal", text, className } = element.props;
  return (
    <Divider orientation={orientation} className={className}>
      {text}
    </Divider>
  );
}

export { ShinyDivider as Divider };
