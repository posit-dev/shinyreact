import ImageList from "@mui/material/ImageList";
import ImageListItem from "@mui/material/ImageListItem";

// --- shinyreact bridge ---
// Display: data-driven grid of images from `items`.
function ShinyImageList({ element }) {
  const { items = [], cols = 3, className } = element.props;
  return (
    <ImageList cols={cols} className={className}>
      {items.map((it, i) => (
        <ImageListItem key={i}>
          <img src={it.src} alt={it.alt} loading="lazy" />
        </ImageListItem>
      ))}
    </ImageList>
  );
}

export { ShinyImageList as ImageList };
