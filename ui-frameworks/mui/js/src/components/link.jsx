import Link from "@mui/material/Link";

// --- shinyreact bridge ---
// Display: renders a static link.
function ShinyLink({ element }) {
  const { label, href, target, className } = element.props;
  return (
    <Link href={href} target={target} className={className}>
      {label}
    </Link>
  );
}

export { ShinyLink as Link };
