import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import * as React from "react";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Hybrid: tabs metadata drives the bar; positional children are the panels.
// Server reads input.<input_id>() as the selected tab value.
function ShinyTabs({ element, children }) {
  const { input_id, tabs = [], selected, className } = element.props;
  const [value, setValue] = useShinyInput(
    input_id,
    selected ?? tabs[0]?.value ?? "",
  );
  const panels = React.Children.toArray(children);
  return (
    <Box className={className}>
      <Tabs value={value} onChange={(_, v) => setValue(v)}>
        {tabs.map((t) => (
          <Tab key={t.value} value={t.value} label={t.label} />
        ))}
      </Tabs>
      {tabs.map(
        (t, i) =>
          value === t.value && (
            <Box key={t.value} sx={{ p: 2 }}>
              {panels[i]}
            </Box>
          ),
      )}
    </Box>
  );
}

export { ShinyTabs as Tabs };
