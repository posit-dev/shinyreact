import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import { useSetShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Display: a list of items. With input_id, items become clickable and the
// server reads the selected item via input.<input_id>().
function ShinyList({ element }) {
  const { input_id, items = [], className } = element.props;
  const rows = items.map((it) =>
    typeof it === "string" ? { primary: it } : it,
  );
  const _set = useSetShinyInput(input_id ?? "__noop_list__", null, {
    debounceMs: 0,
    priority: "event",
  });
  const setSelected = input_id ? _set : null;
  return (
    <List className={className}>
      {rows.map((r, i) =>
        setSelected ? (
          <ListItemButton
            key={i}
            onClick={() => setSelected({ value: r.primary, nonce: Date.now() })}
          >
            <ListItemText primary={r.primary} secondary={r.secondary} />
          </ListItemButton>
        ) : (
          <ListItem key={i}>
            <ListItemText primary={r.primary} secondary={r.secondary} />
          </ListItem>
        ),
      )}
    </List>
  );
}

export { ShinyList as List };
