import { cn } from "@/lib/utils";

// --- shadcn source (converted from TS) ---

function Skeleton({ className, ...props }) {
  return <div data-slot="skeleton" className={cn("animate-pulse rounded-md bg-accent", className)} {...props} />;
}

// --- shinyreact bridge ---
// A loading placeholder. Size it via className (e.g. "h-4 w-32"). No input.

function ShinySkeleton({ element }) {
  const { className } = element.props;
  return <Skeleton className={className} />;
}

export { ShinySkeleton as Skeleton };
