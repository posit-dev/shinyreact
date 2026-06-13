import Tooltip from "@mui/material/Tooltip";

// --- shinyreact bridge ---
// Container: wraps children with a hover tooltip. Tooltip needs a single
// child element, so children are wrapped in a span.
function ShinyTooltip({ element, children }) {
  const { title, className } = element.props;
  return (
    <Tooltip title={title}>
      <span className={className}>{children}</span>
    </Tooltip>
  );
}

export { ShinyTooltip as Tooltip };
