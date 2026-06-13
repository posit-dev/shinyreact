import Skeleton from "@mui/material/Skeleton";

// --- shinyreact bridge ---
// Display: placeholder shape while content loads.
function ShinySkeleton({ element }) {
  const { variant = "text", width, height, className } = element.props;
  return (
    <Skeleton
      variant={variant}
      width={width}
      height={height}
      className={className}
    />
  );
}

export { ShinySkeleton as Skeleton };
