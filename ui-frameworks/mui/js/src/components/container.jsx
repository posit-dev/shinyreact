import Container from "@mui/material/Container";

// --- shinyreact bridge ---
// Container: centered, width-constrained MUI Container.
function ShinyContainer({ element, children }) {
  const { max_width = "md", className } = element.props;
  return (
    <Container maxWidth={max_width} className={className}>
      {children}
    </Container>
  );
}

export { ShinyContainer as Container };
