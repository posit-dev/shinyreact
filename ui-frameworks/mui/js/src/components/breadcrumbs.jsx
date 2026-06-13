import Breadcrumbs from "@mui/material/Breadcrumbs";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";

// --- shinyreact bridge ---
// Display: renders a static breadcrumb trail from {label, href} items.
function ShinyBreadcrumbs({ element }) {
  const { items = [], className } = element.props;
  return (
    <Breadcrumbs className={className}>
      {items.map((it, i) =>
        i === items.length - 1 ? (
          <Typography key={i} color="text.primary">
            {it.label}
          </Typography>
        ) : (
          <Link key={i} href={it.href} underline="hover">
            {it.label}
          </Link>
        ),
      )}
    </Breadcrumbs>
  );
}

export { ShinyBreadcrumbs as Breadcrumbs };
