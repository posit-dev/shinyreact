import { ScrollArea as ScrollAreaPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";
function ScrollArea({
  className,
  children,
  ...props
}) {
  return <ScrollAreaPrimitive.Root
    data-slot="scroll-area"
    className={cn("relative", className)}
    {...props}
  ><ScrollAreaPrimitive.Viewport
    data-slot="scroll-area-viewport"
    className="size-full rounded-[inherit] transition-[color,box-shadow] outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-1"
  >{children}</ScrollAreaPrimitive.Viewport><ScrollBar /><ScrollAreaPrimitive.Corner /></ScrollAreaPrimitive.Root>;
}
function ScrollBar({
  className,
  orientation = "vertical",
  ...props
}) {
  return <ScrollAreaPrimitive.ScrollAreaScrollbar
    data-slot="scroll-area-scrollbar"
    orientation={orientation}
    className={cn(
      "flex touch-none p-px transition-colors select-none",
      orientation === "vertical" && "h-full w-2.5 border-l border-l-transparent",
      orientation === "horizontal" && "h-2.5 flex-col border-t border-t-transparent",
      className
    )}
    {...props}
  ><ScrollAreaPrimitive.ScrollAreaThumb
    data-slot="scroll-area-thumb"
    className="relative flex-1 rounded-full bg-border"
  /></ScrollAreaPrimitive.ScrollAreaScrollbar>;
}

// --- shinyreact bridge ---
// Container: no Shiny state. Wraps children in a styled scrollable box.
function ShinyScrollArea({ element, children }) {
  const { height = "300px", orientation = "vertical", className } = element.props;
  return (
    <ScrollArea style={{ height }} className={className}>
      {children}
      {orientation === "both" && <ScrollBar orientation="horizontal" />}
    </ScrollArea>
  );
}

export { ShinyScrollArea as ScrollArea };
