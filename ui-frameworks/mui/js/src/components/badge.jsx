import Badge from "@mui/material/Badge";

// --- shinyreact bridge ---
// Container: overlays a small badge on its children.
function ShinyBadge({ element, children }) {
  const { badge_content, color = "primary", className } = element.props;
  return (
    <Badge badgeContent={badge_content} color={color} className={className}>
      {children}
    </Badge>
  );
}

export { ShinyBadge as Badge };
