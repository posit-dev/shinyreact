import * as React from "react";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";

// --- shinyreact bridge ---
// Hybrid: data-driven `items` define the panels; positional children fill bodies.
function ShinyAccordion({ element, children }) {
  const { items = [], className } = element.props;
  const panels = React.Children.toArray(children);
  return (
    <div className={className}>
      {items.map((it, i) => (
        <Accordion key={it.value}>
          <AccordionSummary>{it.title}</AccordionSummary>
          <AccordionDetails>{panels[i]}</AccordionDetails>
        </Accordion>
      ))}
    </div>
  );
}

export { ShinyAccordion as Accordion };
