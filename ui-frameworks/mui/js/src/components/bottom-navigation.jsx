import BottomNavigation from "@mui/material/BottomNavigation";
import BottomNavigationAction from "@mui/material/BottomNavigationAction";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as the selected item value.
function ShinyBottomNavigation({ element }) {
  const { input_id, items = [], className } = element.props;
  const [value, setValue] = useShinyInput(input_id, items[0]?.value);
  return (
    <BottomNavigation
      value={value}
      onChange={(_, v) => setValue(v)}
      showLabels
      className={className}
    >
      {items.map((it) => (
        <BottomNavigationAction key={it.value} value={it.value} label={it.label} />
      ))}
    </BottomNavigation>
  );
}

export { ShinyBottomNavigation as BottomNavigation };
