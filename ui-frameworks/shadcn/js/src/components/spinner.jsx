import { Loader2Icon } from "lucide-react";
import { cn } from "@/lib/utils";
function Spinner({ className, ...props }) {
  return <Loader2Icon
    role="status"
    aria-label="Loading"
    className={cn("size-4 animate-spin", className)}
    {...props}
  />;
}

// --- shinyreact bridge ---
// A loading spinner. Size via className (e.g. "size-6"). Display-only.

function ShinySpinner({ element }) {
  const { className } = element.props;
  return <Spinner className={className} />;
}

export { ShinySpinner as Spinner };
