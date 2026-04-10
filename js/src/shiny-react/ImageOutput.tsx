import { useCallback, useEffect, useRef, useState } from "react";
import { useShinyInput, useShinyOutput } from "./use-shiny";
import { createDebouncedFn } from "./utils";
import {
  applyNamespace,
  useShinyModuleNamespace,
} from "./ShinyModuleContext";

export type ImageData = {
  src: string;
  width: number;
  height: number;
  coordmap: {
    panels: {
      panel: number;
      row: number;
      col: number;
      domain: {
        left: number;
        right: number;
        bottom: number;
        top: number;
      };
      range: {
        left: number;
        right: number;
        bottom: number;
        top: number;
      };
      log: {
        x: string | null;
        y: string | null;
      };
      mapping: {
        x: string | null;
        y: string | null;
      };
    }[];
    dims: {
      width: number;
      height: number;
    };
  };
};

/**
 * A React component for displaying Shiny image outputs with dynamic sizing
 * capabilities.
 *
 * Unlike typical web images that have an inherent size, this component tells
 * the server to generate an image that is sized to fit the dimensions of the
 * <img> element which is rendered by the component. This means that the element
 * must have a width and height, either through CSS or through the width and
 * height props.
 *
 * For vertical stretching, you can use height: "100%" inside a flex container,
 * or use viewport units like "100vh" for full height
 *
 * @param props - The component props
 * @param props.id - The Shiny output ID that corresponds to a renderImage()
 *    call on the server
 * @param props.className - Optional CSS class name to apply to the img element
 * @param props.width - Optional width as a CSS size string (e.g., "300px",
 *    "50%", "auto"). If provided, sets the width attribute on the img tag. If
 *    not provided, the width should be controlled via CSS applied to this
 *    element.
 * @param props.height - Optional height as a CSS size string (e.g., "200px",
 *    "50vh", "auto"). If provided, sets the height attribute on the img tag. If
 *    not provided, the height should be controlled via CSS applied to this
 *    element.
 * @param props.debounceMs - Optional debounce delay in milliseconds for
 *    dimension change detection (default: 400ms). Controls how long to wait
 *    after a resize event before sending updated dimensions to Shiny. Higher
 *    values reduce server load but may delay updates.
 * @param props.namespace - Optional namespace override for Shiny module
 *    support. If provided, overrides the namespace from ShinyModuleProvider
 *    context. Pass `null` to explicitly disable namespacing even when inside
 *    a provider.
 * @param props.onRecalculating - Optional callback function that gets called
 *    whenever the recalculation status changes. Receives a boolean indicating
 *    whether the image is currently recalculating.
 *
 * @remarks
 * The component automatically:
 * - Tracks the rendered dimensions of the image and sends them to Shiny via
 *   clientData
 * - Updates Shiny when the image size changes (using ResizeObserver with
 *   debouncing)
 * - Hides the image when Shiny sets the hidden state
 * - Handles image load events to ensure accurate dimension reporting
 *
 * The server-side renderImage() function receives the client dimensions and can
 * use them to generate appropriately sized images.
 *
 * Note that if you use two ImageOutputs with the same ID, the server will
 * generate only one image at the width and height for one of them; both
 * ImageOutputs will receive the same image data. but it will only be sized for
 * one of the ImageOutputs.
 *
 * @example
 * ```tsx
 * // With explicit dimensions
 * <ImageOutput id="myplot" width="100%" height="300px" />
 *
 * // With CSS-controlled dimensions
 * <ImageOutput id="myplot" className="output-image" />
 * ```
 *
 * @example CSS for responsive sizing:
 * ```
 * // Full viewport height
 * <ImageOutput id="myplot" className="full-height-image" />
 *
 * .full-height-image {
 *   width: 100%;
 *   height: 100dvh;
 * }
 * ```
 *
 * @example CSS for height to be determined by container:
 * ```
 * <div className="flex-container">
 *   <ImageOutput id="myplot" className="flex-image" />
 * </div>
 *
 * .flex-container {
 *   display: flex;
 *   flex-direction: column;
 * }
 *
 * .flex-image {
 *   flex: 1;
 *   width: 100%;
 *   height: 100%;
 *   min-height: 300px;
 * }
 * ```
 */
export function ImageOutput({
  id,
  className,
  width,
  height,
  debounceMs = 400,
  onRecalculating,
  namespace: explicitNamespace,
}: {
  id: string;
  className?: string;
  width?: string;
  height?: string;
  debounceMs?: number;
  onRecalculating?: (isRecalculating: boolean) => void;
  namespace?: string | null;
}) {
  // Apply namespace from context or explicit option
  const contextNamespace = useShinyModuleNamespace();
  const namespace = explicitNamespace ?? contextNamespace;
  const namespacedId = applyNamespace(id, namespace);

  // IDs below already have the namespace embedded (via namespacedId), so we
  // suppress the hooks' own context-based namespacing to avoid double-prefixing.
  const skipNs = { namespace: null };
  const [imgWidth, setImgWidth] = useShinyInput<number | null>(
    `.clientdata_output_${namespacedId}_width`,
    null,
    skipNs,
  );
  const [imgHeight, setImgHeight] = useShinyInput<number | null>(
    `.clientdata_output_${namespacedId}_height`,
    null,
    skipNs,
  );
  const [imgHidden] = useShinyInput<boolean>(
    `.clientdata_output_${namespacedId}_hidden`,
    false,
    skipNs,
  );
  const [imgData, imgRecalculating] = useShinyOutput<ImageData>(namespacedId, undefined, skipNs);

  // Create a reference to the img element to access its properties
  const imgRef = useRef<HTMLImageElement>(null);

  // Track when the image data changes
  const [imageVersion, setImageVersion] = useState(0);

  // Update the version when imgData changes
  useEffect(() => {
    if (imgData) {
      setImageVersion((prev) => prev + 1);
    }
  }, [imgData]);

  // Notify parent component when recalculation status changes
  useEffect(() => {
    if (onRecalculating) {
      onRecalculating(imgRecalculating);
    }
  }, [imgRecalculating, onRecalculating]);

  // Handle image load and dimension changes.
  // Skip 0×0 dimensions (element is hidden via display:none) to avoid
  // triggering a server re-render that would invalidate the current image.
  const handleImageLoad = useCallback(() => {
    if (imgRef.current) {
      const width = imgRef.current.clientWidth;
      const height = imgRef.current.clientHeight;
      if (width > 0 && height > 0) {
        setImgWidth(width);
        setImgHeight(height);
      }
    }
  }, [setImgWidth, setImgHeight]);

  // Set up a mutation observer to detect image dimension changes
  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    // Set initial dimensions when the image first loads
    img.addEventListener("load", handleImageLoad);

    // Create a debounced version of handleImageLoad with 200ms delay
    const debouncedHandleResize = createDebouncedFn(() => {
      if (img && img.complete) {
        handleImageLoad();
      }
    }, debounceMs);

    // Create a ResizeObserver to detect size changes
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.target === img) {
          debouncedHandleResize();
        }
      }
    });

    resizeObserver.observe(img);

    return () => {
      img.removeEventListener("load", handleImageLoad);
      resizeObserver.disconnect();
      debouncedHandleResize.cancel();
    };
  }, [
    imgRef,
    imageVersion,
    setImgWidth,
    setImgHeight,
    debounceMs,
    handleImageLoad,
  ]);

  if (imgHidden) {
    return null;
  }

  // Show a placeholder while waiting for the first image or during recalculation
  if (!imgData) {
    return (
      <div
        className={className}
        style={{
          width: width,
          height: height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#9ca3af",
        }}
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          style={{
            animation: "spin 1s linear infinite",
          }}
        >
          <circle
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeDasharray="31.4 31.4"
            strokeLinecap="round"
          />
        </svg>
      </div>
    );
  }

  return (
    <img
      ref={imgRef}
      src={imgData.src}
      alt=""
      className={className}
      style={{
        width: width,
        height: height,
      }}
      onLoad={handleImageLoad}
    />
  );
}
