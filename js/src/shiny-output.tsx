import React, { useEffect, useRef } from "react";

export interface ShinyOutputProps
  extends React.HTMLAttributes<HTMLElement> {
  id: string;
  tagName?: string;
}

export function ShinyOutput({
  id,
  tagName = "div",
  ...rest
}: ShinyOutputProps): React.JSX.Element {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || !window.Shiny?.bindAll) return;
    void window.Shiny.bindAll(el);
    return () => {
      window.Shiny?.unbindAll?.(el);
    };
  }, [id, tagName]);

  return (
    <div ref={ref}>
      {React.createElement(tagName, { id, ...rest })}
    </div>
  );
}
