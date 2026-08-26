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
export declare function ImageOutput({ id, className, width, height, debounceMs, onRecalculating, namespace: explicitNamespace, }: {
    id: string;
    className?: string;
    width?: string;
    height?: string;
    debounceMs?: number;
    onRecalculating?: (isRecalculating: boolean) => void;
    namespace?: string | null;
}): import("react/jsx-runtime").JSX.Element | null;
