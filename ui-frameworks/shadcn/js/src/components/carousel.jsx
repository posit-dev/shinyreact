import * as React from "react";
import useEmblaCarousel from "embla-carousel-react";
import { useShinyInput } from "shinyreact";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/lib/button-base";
const CarouselContext = React.createContext(null);
function useCarousel() {
  const context = React.useContext(CarouselContext);
  if (!context) {
    throw new Error("useCarousel must be used within a <Carousel />");
  }
  return context;
}
function Carousel({
  orientation = "horizontal",
  opts,
  setApi,
  plugins,
  className,
  children,
  ...props
}) {
  const [carouselRef, api] = useEmblaCarousel(
    {
      ...opts,
      axis: orientation === "horizontal" ? "x" : "y"
    },
    plugins
  );
  const [canScrollPrev, setCanScrollPrev] = React.useState(false);
  const [canScrollNext, setCanScrollNext] = React.useState(false);
  const onSelect = React.useCallback((api2) => {
    if (!api2) return;
    setCanScrollPrev(api2.canScrollPrev());
    setCanScrollNext(api2.canScrollNext());
  }, []);
  const scrollPrev = React.useCallback(() => {
    api?.scrollPrev();
  }, [api]);
  const scrollNext = React.useCallback(() => {
    api?.scrollNext();
  }, [api]);
  const handleKeyDown = React.useCallback(
    (event) => {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        scrollPrev();
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        scrollNext();
      }
    },
    [scrollPrev, scrollNext]
  );
  React.useEffect(() => {
    if (!api || !setApi) return;
    setApi(api);
  }, [api, setApi]);
  React.useEffect(() => {
    if (!api) return;
    onSelect(api);
    api.on("reInit", onSelect);
    api.on("select", onSelect);
    return () => {
      api?.off("select", onSelect);
    };
  }, [api, onSelect]);
  return <CarouselContext.Provider
    value={{
      carouselRef,
      api,
      opts,
      orientation: orientation || (opts?.axis === "y" ? "vertical" : "horizontal"),
      scrollPrev,
      scrollNext,
      canScrollPrev,
      canScrollNext
    }}
  ><div
    onKeyDownCapture={handleKeyDown}
    className={cn("relative", className)}
    role="region"
    aria-roledescription="carousel"
    data-slot="carousel"
    {...props}
  >{children}</div></CarouselContext.Provider>;
}
function CarouselContent({ className, ...props }) {
  const { carouselRef, orientation } = useCarousel();
  return <div
    ref={carouselRef}
    className="overflow-hidden"
    data-slot="carousel-content"
  ><div
    className={cn(
      "flex",
      orientation === "horizontal" ? "-ml-4" : "-mt-4 flex-col",
      className
    )}
    {...props}
  /></div>;
}
function CarouselItem({ className, ...props }) {
  const { orientation } = useCarousel();
  return <div
    role="group"
    aria-roledescription="slide"
    data-slot="carousel-item"
    className={cn(
      "min-w-0 shrink-0 grow-0 basis-full",
      orientation === "horizontal" ? "pl-4" : "pt-4",
      className
    )}
    {...props}
  />;
}
function CarouselPrevious({
  className,
  variant = "outline",
  size = "icon",
  ...props
}) {
  const { orientation, scrollPrev, canScrollPrev } = useCarousel();
  return <Button
    data-slot="carousel-previous"
    variant={variant}
    size={size}
    className={cn(
      "absolute size-8 rounded-full",
      orientation === "horizontal" ? "top-1/2 -left-12 -translate-y-1/2" : "-top-12 left-1/2 -translate-x-1/2 rotate-90",
      className
    )}
    disabled={!canScrollPrev}
    onClick={scrollPrev}
    {...props}
  ><ArrowLeft /><span className="sr-only">Previous slide</span></Button>;
}
function CarouselNext({
  className,
  variant = "outline",
  size = "icon",
  ...props
}) {
  const { orientation, scrollNext, canScrollNext } = useCarousel();
  return <Button
    data-slot="carousel-next"
    variant={variant}
    size={size}
    className={cn(
      "absolute size-8 rounded-full",
      orientation === "horizontal" ? "top-1/2 -right-12 -translate-y-1/2" : "-bottom-12 left-1/2 -translate-x-1/2 rotate-90",
      className
    )}
    disabled={!canScrollNext}
    onClick={scrollNext}
    {...props}
  ><ArrowRight /><span className="sr-only">Next slide</span></Button>;
}

// --- shinyreact bridge ---
// TODO(you): choose the component type and wire it. Types:
//   Display      -> no hook; read props.
//   Input        -> useShinyInput(input_id, default)
//   Action       -> useShinyInput(id, 0, { debounceMs: 0, priority: "event" })
//   Overlay      -> useShinyInput(id, false) for open state + children
//   Collection   -> items prop array (see dropdown-menu.jsx)
//   Hybrid/Push  -> see tabs.jsx / sonner.jsx
// Forward className to the root via the component (it merges with cn()).
// Hybrid: children = slides (each wrapped in CarouselItem); input_id (optional)
// tracks the current 0-based slide index on the server.
// Props: input_id?, orientation, loop, className.
function ShinyCarousel({ element, children }) {
  const {
    input_id,
    orientation = "horizontal",
    loop = false,
    className,
  } = element.props;
  const [, _setValue] = useShinyInput(input_id ?? "__noop_carousel__", 0);
  const setValue = input_id ? _setValue : null;
  const childArray = React.Children.toArray(children);

  return (
    <Carousel
      orientation={orientation}
      opts={{ loop }}
      setApi={(api) => {
        if (!api || !setValue) return;
        api.on("select", (a) => setValue(a.selectedScrollSnap()));
      }}
      className={className}
    >
      <CarouselContent>
        {childArray.map((child, i) => (
          <CarouselItem key={i}>{child}</CarouselItem>
        ))}
      </CarouselContent>
      <CarouselPrevious />
      <CarouselNext />
    </Carousel>
  );
}

export { ShinyCarousel as Carousel };
