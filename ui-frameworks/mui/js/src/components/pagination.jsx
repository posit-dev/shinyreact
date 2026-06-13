import Pagination from "@mui/material/Pagination";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as the current page number.
function ShinyPagination({ element }) {
  const { input_id, count = 10, className } = element.props;
  const [value, setValue] = useShinyInput(input_id, 1);
  return (
    <Pagination
      count={count}
      page={value ?? 1}
      onChange={(_, p) => setValue(p)}
      className={className}
    />
  );
}

export { ShinyPagination as Pagination };
