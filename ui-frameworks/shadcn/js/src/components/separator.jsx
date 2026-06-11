import { cn } from "@/lib/utils";

export function Separator({ element }) {
  const { orientation = "horizontal", className } = element.props;
  return (
    <div
      role="separator"
      className={cn(
        "shrink-0 bg-border",
        orientation === "vertical" ? "h-full w-px" : "h-px w-full",
        className
      )}
    />
  );
}
