import Avatar from "@mui/material/Avatar";

// --- shinyreact bridge ---
// Display: an avatar with an optional image, alt text, and fallback text.
function ShinyAvatar({ element }) {
  const { src, alt, text, className } = element.props;
  return (
    <Avatar src={src} alt={alt} className={className}>
      {text}
    </Avatar>
  );
}

export { ShinyAvatar as Avatar };
