import { Drawer as DrawerPrimitive } from "vaul";
import { cn } from "@/lib/utils";
import { useShinyInput } from "shinyreact";
import { TriggerButton } from "@/lib/trigger-button";
function Drawer({
  ...props
}) {
  return <DrawerPrimitive.Root data-slot="drawer" {...props} />;
}
function DrawerTrigger({
  ...props
}) {
  return <DrawerPrimitive.Trigger data-slot="drawer-trigger" {...props} />;
}
function DrawerPortal({
  ...props
}) {
  return <DrawerPrimitive.Portal data-slot="drawer-portal" {...props} />;
}
function DrawerClose({
  ...props
}) {
  return <DrawerPrimitive.Close data-slot="drawer-close" {...props} />;
}
function DrawerOverlay({
  className,
  ...props
}) {
  return <DrawerPrimitive.Overlay
    data-slot="drawer-overlay"
    className={cn(
      "fixed inset-0 z-50 bg-black/50 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:animate-in data-[state=open]:fade-in-0",
      className
    )}
    {...props}
  />;
}
function DrawerContent({
  className,
  children,
  ...props
}) {
  return <DrawerPortal data-slot="drawer-portal"><DrawerOverlay /><DrawerPrimitive.Content
    data-slot="drawer-content"
    className={cn(
      "group/drawer-content fixed z-50 flex h-auto flex-col bg-background",
      "data-[vaul-drawer-direction=top]:inset-x-0 data-[vaul-drawer-direction=top]:top-0 data-[vaul-drawer-direction=top]:mb-24 data-[vaul-drawer-direction=top]:max-h-[80vh] data-[vaul-drawer-direction=top]:rounded-b-lg data-[vaul-drawer-direction=top]:border-b",
      "data-[vaul-drawer-direction=bottom]:inset-x-0 data-[vaul-drawer-direction=bottom]:bottom-0 data-[vaul-drawer-direction=bottom]:mt-24 data-[vaul-drawer-direction=bottom]:max-h-[80vh] data-[vaul-drawer-direction=bottom]:rounded-t-lg data-[vaul-drawer-direction=bottom]:border-t",
      "data-[vaul-drawer-direction=right]:inset-y-0 data-[vaul-drawer-direction=right]:right-0 data-[vaul-drawer-direction=right]:w-3/4 data-[vaul-drawer-direction=right]:border-l data-[vaul-drawer-direction=right]:sm:max-w-sm",
      "data-[vaul-drawer-direction=left]:inset-y-0 data-[vaul-drawer-direction=left]:left-0 data-[vaul-drawer-direction=left]:w-3/4 data-[vaul-drawer-direction=left]:border-r data-[vaul-drawer-direction=left]:sm:max-w-sm",
      className
    )}
    {...props}
  ><div className="mx-auto mt-4 hidden h-2 w-[100px] shrink-0 rounded-full bg-muted group-data-[vaul-drawer-direction=bottom]/drawer-content:block" />{children}</DrawerPrimitive.Content></DrawerPortal>;
}
function DrawerHeader({ className, ...props }) {
  return <div
    data-slot="drawer-header"
    className={cn(
      "flex flex-col gap-0.5 p-4 group-data-[vaul-drawer-direction=bottom]/drawer-content:text-center group-data-[vaul-drawer-direction=top]/drawer-content:text-center md:gap-1.5 md:text-left",
      className
    )}
    {...props}
  />;
}
function DrawerFooter({ className, ...props }) {
  return <div
    data-slot="drawer-footer"
    className={cn("mt-auto flex flex-col gap-2 p-4", className)}
    {...props}
  />;
}
function DrawerTitle({
  className,
  ...props
}) {
  return <DrawerPrimitive.Title
    data-slot="drawer-title"
    className={cn("font-semibold text-foreground", className)}
    {...props}
  />;
}
function DrawerDescription({
  className,
  ...props
}) {
  return <DrawerPrimitive.Description
    data-slot="drawer-description"
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />;
}

// --- shinyreact bridge ---
function ShinyDrawer({ element, children }) {
  const { input_id, trigger_label = "Open", direction = "bottom", title, description, className } = element.props;
  const [open, setOpen] = useShinyInput(input_id, false);
  return (
    <Drawer open={!!open} onOpenChange={setOpen} direction={direction}>
      <DrawerTrigger asChild>
        <TriggerButton>{trigger_label}</TriggerButton>
      </DrawerTrigger>
      <DrawerContent className={className}>
        {(title || description) && (
          <DrawerHeader>
            {title && <DrawerTitle>{title}</DrawerTitle>}
            {description && <DrawerDescription>{description}</DrawerDescription>}
          </DrawerHeader>
        )}
        <div className="flex flex-col gap-4 p-4 pb-6">{children}</div>
      </DrawerContent>
    </Drawer>
  );
}

export { ShinyDrawer as Drawer };
