import * as React from "react";
import { CheckIcon, ChevronRightIcon, CircleIcon } from "lucide-react";
import { DropdownMenu as DropdownMenuPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";
import { TriggerButton } from "@/lib/trigger-button";
import { useShinyInput, useSetShinyInput } from "shinyreact";

// --- shadcn source (converted from TS) ---

function DropdownMenu({ ...props }) {
  return <DropdownMenuPrimitive.Root data-slot="dropdown-menu" {...props} />;
}

function DropdownMenuPortal({ ...props }) {
  return <DropdownMenuPrimitive.Portal data-slot="dropdown-menu-portal" {...props} />;
}

function DropdownMenuTrigger({ ...props }) {
  return <DropdownMenuPrimitive.Trigger data-slot="dropdown-menu-trigger" {...props} />;
}

function DropdownMenuContent({ className, sideOffset = 4, ...props }) {
  return (
    <DropdownMenuPrimitive.Portal>
      <DropdownMenuPrimitive.Content
        data-slot="dropdown-menu-content"
        sideOffset={sideOffset}
        className={cn(
          "z-50 max-h-(--radix-dropdown-menu-content-available-height) min-w-[8rem] origin-(--radix-dropdown-menu-content-transform-origin) overflow-x-hidden overflow-y-auto rounded-md border bg-popover p-1 text-popover-foreground shadow-md data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
          className
        )}
        {...props}
      />
    </DropdownMenuPrimitive.Portal>
  );
}

function DropdownMenuGroup({ ...props }) {
  return <DropdownMenuPrimitive.Group data-slot="dropdown-menu-group" {...props} />;
}

function DropdownMenuItem({ className, inset, variant = "default", ...props }) {
  return (
    <DropdownMenuPrimitive.Item
      data-slot="dropdown-menu-item"
      data-inset={inset}
      data-variant={variant}
      className={cn(
        "relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 data-[inset]:pl-8 data-[variant=destructive]:text-destructive data-[variant=destructive]:focus:bg-destructive/10 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 [&_svg:not([class*='text-'])]:text-muted-foreground",
        className
      )}
      {...props}
    />
  );
}

function DropdownMenuCheckboxItem({ className, children, checked, ...props }) {
  return (
    <DropdownMenuPrimitive.CheckboxItem
      data-slot="dropdown-menu-checkbox-item"
      className={cn(
        "relative flex cursor-default items-center gap-2 rounded-sm py-1.5 pr-2 pl-8 text-sm outline-hidden select-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      checked={checked}
      {...props}
    >
      <span className="pointer-events-none absolute left-2 flex size-3.5 items-center justify-center">
        <DropdownMenuPrimitive.ItemIndicator>
          <CheckIcon className="size-4" />
        </DropdownMenuPrimitive.ItemIndicator>
      </span>
      {children}
    </DropdownMenuPrimitive.CheckboxItem>
  );
}

function DropdownMenuRadioGroup({ ...props }) {
  return <DropdownMenuPrimitive.RadioGroup data-slot="dropdown-menu-radio-group" {...props} />;
}

function DropdownMenuRadioItem({ className, children, ...props }) {
  return (
    <DropdownMenuPrimitive.RadioItem
      data-slot="dropdown-menu-radio-item"
      className={cn(
        "relative flex cursor-default items-center gap-2 rounded-sm py-1.5 pr-2 pl-8 text-sm outline-hidden select-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}
    >
      <span className="pointer-events-none absolute left-2 flex size-3.5 items-center justify-center">
        <DropdownMenuPrimitive.ItemIndicator>
          <CircleIcon className="size-2 fill-current" />
        </DropdownMenuPrimitive.ItemIndicator>
      </span>
      {children}
    </DropdownMenuPrimitive.RadioItem>
  );
}

function DropdownMenuLabel({ className, inset, ...props }) {
  return (
    <DropdownMenuPrimitive.Label
      data-slot="dropdown-menu-label"
      data-inset={inset}
      className={cn("px-2 py-1.5 text-sm font-medium data-[inset]:pl-8", className)}
      {...props}
    />
  );
}

function DropdownMenuSeparator({ className, ...props }) {
  return (
    <DropdownMenuPrimitive.Separator
      data-slot="dropdown-menu-separator"
      className={cn("-mx-1 my-1 h-px bg-border", className)}
      {...props}
    />
  );
}

function DropdownMenuSub({ ...props }) {
  return <DropdownMenuPrimitive.Sub data-slot="dropdown-menu-sub" {...props} />;
}

function DropdownMenuSubTrigger({ className, inset, children, ...props }) {
  return (
    <DropdownMenuPrimitive.SubTrigger
      data-slot="dropdown-menu-sub-trigger"
      data-inset={inset}
      className={cn(
        "flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none focus:bg-accent focus:text-accent-foreground data-[inset]:pl-8 data-[state=open]:bg-accent data-[state=open]:text-accent-foreground [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 [&_svg:not([class*='text-'])]:text-muted-foreground",
        className
      )}
      {...props}
    >
      {children}
      <ChevronRightIcon className="ml-auto size-4" />
    </DropdownMenuPrimitive.SubTrigger>
  );
}

function DropdownMenuSubContent({ className, ...props }) {
  return (
    <DropdownMenuPrimitive.SubContent
      data-slot="dropdown-menu-sub-content"
      className={cn(
        "z-50 min-w-[8rem] origin-(--radix-dropdown-menu-content-transform-origin) overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-lg data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
        className
      )}
      {...props}
    />
  );
}

// --- shinyreact bridge ---
// A dropdown menu driven by a data array (not nested Nodes), because a menu is
// fundamentally a structured list of actions, not free-form content.
//
// Props:
//   input_id (str)      — event input. Clicking a plain item sets it to
//                         { value, nonce }. The nonce changes on every click so
//                         repeated clicks of the same item still register.
//   trigger_label (str) — text on the button that opens the menu.
//   items (Item[])      — the menu contents. Item shapes:
//     { type: "item", value, label, disabled?, variant? }       → click event
//     { type: "label", label }                                  → section header
//     { type: "separator" }                                     → divider
//     { type: "checkbox", input_id, label, checked? }           → own bool input
//     { type: "submenu", label, items: [...] }                  → nested (recursive)
//
// Two input kinds coexist in one menu:
//   - plain items are EVENTS  → reported through the menu's own input_id
//   - checkbox items are STATE → each owns a separate boolean input_id
// This mirrors Shiny's distinction between action events and reactive values.

function MenuItems({ items, onSelect }) {
  return items.map((item, i) => {
    switch (item.type) {
      case "label":
        return <DropdownMenuLabel key={i}>{item.label}</DropdownMenuLabel>;

      case "separator":
        return <DropdownMenuSeparator key={i} />;

      case "checkbox":
        return <CheckboxMenuItem key={i} item={item} />;

      case "submenu":
        return (
          <DropdownMenuSub key={i}>
            <DropdownMenuSubTrigger>{item.label}</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <MenuItems items={item.items ?? []} onSelect={onSelect} />
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        );

      case "item":
      default:
        return (
          <DropdownMenuItem
            key={i}
            disabled={item.disabled}
            variant={item.variant}
            onSelect={() => onSelect(item.value)}
          >
            {item.label}
          </DropdownMenuItem>
        );
    }
  });
}

// Checkbox items own their own boolean Shiny input — independent persistent state.
function CheckboxMenuItem({ item }) {
  const [checked, setChecked] = useShinyInput(item.input_id, item.checked ?? false);
  return (
    <DropdownMenuCheckboxItem
      checked={!!checked}
      onCheckedChange={setChecked}
      onSelect={(e) => e.preventDefault()} // keep the menu open when toggling
    >
      {item.label}
    </DropdownMenuCheckboxItem>
  );
}

function ShinyDropdownMenu({ element }) {
  const { input_id, trigger_label = "Open", items = [], className } = element.props;
  // Event input: write-only. Carries the clicked value plus a nonce so that
  // clicking the same item twice still produces a distinct input change.
  const setSelected = useSetShinyInput(input_id, null, { debounceMs: 0, priority: "event" });
  const onSelect = (value) => setSelected({ value, nonce: Date.now() });

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <TriggerButton>{trigger_label}</TriggerButton>
      </DropdownMenuTrigger>
      <DropdownMenuContent className={className}>
        <MenuItems items={items} onSelect={onSelect} />
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export { ShinyDropdownMenu as DropdownMenu };
