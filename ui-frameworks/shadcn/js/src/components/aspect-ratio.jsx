import { AspectRatio as AspectRatioPrimitive } from "radix-ui";
function AspectRatio({
  ...props
}) {
  return <AspectRatioPrimitive.Root data-slot="aspect-ratio" {...props} />;
}

// --- shinyreact bridge ---
// A fixed aspect-ratio container. Props: ratio (num, e.g. 1.7778 for 16/9),
//   className. Children are the content (e.g. an image).

function ShinyAspectRatio({ element, children }) {
  const { ratio = 1, className } = element.props;
  return (
    <AspectRatio ratio={ratio} className={className}>
      {children}
    </AspectRatio>
  );
}

export { ShinyAspectRatio as AspectRatio };
