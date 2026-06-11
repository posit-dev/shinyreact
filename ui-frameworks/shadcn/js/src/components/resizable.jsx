import * as React from "react";
import { GripVerticalIcon } from "lucide-react";
import * as ResizablePrimitive from "react-resizable-panels";
import { cn } from "@/lib/utils";
function ResizablePanelGroup({
  className,
  ...props
}) {
  return <ResizablePrimitive.Group
    data-slot="resizable-panel-group"
    className={cn(
      "flex h-full w-full aria-[orientation=vertical]:flex-col",
      className
    )}
    {...props}
  />;
}
function ResizablePanel({ ...props }) {
  return <ResizablePrimitive.Panel data-slot="resizable-panel" {...props} />;
}
function ResizableHandle({
  withHandle,
  className,
  ...props
}) {
  return <ResizablePrimitive.Separator
    data-slot="resizable-handle"
    className={cn(
      "relative flex w-px items-center justify-center bg-border after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:outline-hidden aria-[orientation=horizontal]:h-px aria-[orientation=horizontal]:w-full aria-[orientation=horizontal]:after:left-0 aria-[orientation=horizontal]:after:h-1 aria-[orientation=horizontal]:after:w-full aria-[orientation=horizontal]:after:translate-x-0 aria-[orientation=horizontal]:after:-translate-y-1/2 [&[aria-orientation=horizontal]>div]:rotate-90",
      className
    )}
    {...props}
  >{withHandle && <div className="z-10 flex h-4 w-3 items-center justify-center rounded-xs border bg-border"><GripVerticalIcon className="size-2.5" /></div>}</ResizablePrimitive.Separator>;
}

// --- shinyreact bridge ---
// Container: no Shiny state. Renders ResizablePanelGroup with N panels separated
// by handles. Children are matched to panels positionally.
// Props: orientation ("horizontal"|"vertical"), panels ([{default_size?, min_size?}]),
//   handle (show grip handle icon, default true), className.
function ShinyResizable({ element, children }) {
  const {
    orientation = "horizontal",
    panels = [],
    handle = true,
    className,
  } = element.props;
  const childArray = React.Children.toArray(children);
  const count = Math.max(childArray.length, panels.length, 2);
  return (
    <ResizablePanelGroup orientation={orientation} className={className}>
      {Array.from({ length: count }, (_, i) => (
        <React.Fragment key={i}>
          {i > 0 && <ResizableHandle withHandle={handle} />}
          <ResizablePanel
            defaultSize={panels[i]?.default_size ?? 100 / count}
            minSize={panels[i]?.min_size ?? 10}
          >
            {childArray[i]}
          </ResizablePanel>
        </React.Fragment>
      ))}
    </ResizablePanelGroup>
  );
}

export { ShinyResizable as Resizable };
