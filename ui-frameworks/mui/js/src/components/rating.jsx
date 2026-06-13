import Rating from "@mui/material/Rating";
import { useShinyInput } from "shinyreact";

// --- shinyreact bridge ---
// Input: server reads input.<input_id>() as the current rating number.
function ShinyRating({ element }) {
  const { input_id, max = 5, precision = 1, className } = element.props;
  const [value, setValue] = useShinyInput(input_id, 0);
  return (
    <Rating
      value={value ?? 0}
      max={max}
      precision={precision}
      onChange={(_, v) => setValue(v)}
      className={className}
    />
  );
}

export { ShinyRating as Rating };
