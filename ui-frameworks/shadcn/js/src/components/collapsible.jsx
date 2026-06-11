import { Collapsible as CollapsiblePrimitive } from "radix-ui";
import { TriggerButton } from "@/lib/trigger-button";
import { useShinyInput } from "@/hooks";

function Collapsible({
  ...props
}) {
  return <CollapsiblePrimitive.Root data-slot="collapsible" {...props} />;
}
function CollapsibleTrigger({
  ...props
}) {
  return <CollapsiblePrimitive.CollapsibleTrigger
    data-slot="collapsible-trigger"
    {...props}
  />;
}
function CollapsibleContent({
  ...props
}) {
  return <CollapsiblePrimitive.CollapsibleContent
    data-slot="collapsible-content"
    {...props}
  />;
}

// --- shinyreact bridge ---
// A disclosure: a trigger button reveals/hides its children. Server reads
// input.<input_id>() as a boolean (open). Props: input_id, trigger_label,
//   open (initial bool), className. Children are the collapsible content.

function ShinyCollapsible({ element, children }) {
  const { input_id, trigger_label = "Toggle", open: defaultOpen = false, className } = element.props;
  const [open, setOpen] = useShinyInput(input_id, defaultOpen);
  return (
    <Collapsible open={!!open} onOpenChange={setOpen} className={className}>
      <CollapsibleTrigger asChild>
        <TriggerButton>{trigger_label}</TriggerButton>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2">{children}</CollapsibleContent>
    </Collapsible>
  );
}

export { ShinyCollapsible as Collapsible };
