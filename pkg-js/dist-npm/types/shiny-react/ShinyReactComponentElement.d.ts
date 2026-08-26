import { type Root } from "react-dom/client";
/**
 * Base class for creating custom elements that render React components
 * with automatic Shiny integration.
 *
 * Features:
 * - Automatic namespace support via ShinyModuleProvider (uses element's id)
 * - Slot preservation for blended React + Shiny content
 * - Config parsing from data-* attributes (with JSON auto-parsing)
 * - Proper Shiny binding lifecycle (bindAll/unbindAll)
 * - Default slot capture: When no [data-slot] elements are found, all children
 *   are captured under the reserved slot name "__children__"
 *
 * @example Simple widget (no slots):
 * ```typescript
 * class MyCounterElement extends ShinyReactComponentElement {
 *   static component = CounterWidget;
 * }
 * customElements.define('my-counter', MyCounterElement);
 * ```
 *
 * @example Blended component (with slots):
 * ```typescript
 * class MySidebarElement extends ShinyReactComponentElement {
 *   static component = SidebarLayout;
 *
 *   protected render() {
 *     return <SidebarLayout {...this.getConfig()} onSlotMount={this.onSlotMount} />;
 *   }
 * }
 * customElements.define('my-sidebar', MySidebarElement);
 * ```
 *
 * @example Skip clearing innerHTML (rare):
 * ```typescript
 * class MyOverlayElement extends ShinyReactComponentElement {
 *   protected clearContent() {} // no-op
 * }
 * ```
 */
export declare class ShinyReactComponentElement extends HTMLElement {
    protected root: Root | null;
    protected slotContents: Map<string, Node[]>;
    /**
     * The React component to render. Set this on your subclass.
     * @example
     * ```typescript
     * class MyElement extends ShinyReactComponentElement {
     *   static component = MyReactComponent;
     * }
     * ```
     */
    static component: React.ComponentType<Record<string, unknown>> | null;
    /**
     * Captures children with [data-slot] attribute, storing their contents
     * keyed by slot name. Called automatically in connectedCallback.
     *
     * Named slots are captured by their `data-slot` attribute value.
     * All remaining direct children (without a `data-slot` attribute) are
     * captured under the reserved slot name "__children__".
     *
     * @param selector CSS selector for slot containers (default: '[data-slot]')
     * @returns Map of slot names to their child nodes
     */
    protected captureSlots(selector?: string): Map<string, Node[]>;
    /**
     * Moves captured slot content into a container element and initializes
     * Shiny bindings. Call this from your React component via onSlotMount callback.
     *
     * @param slotName The slot identifier (from data-slot attribute)
     * @param container The DOM element to move content into
     */
    protected mountSlot(slotName: string, container: HTMLElement | null): Promise<void>;
    /**
     * Bound callback for mounting slots. Pass this to your React component
     * to handle slot content mounting.
     *
     * @example
     * ```typescript
     * protected render() {
     *   return <MyLayout onSlotMount={this.onSlotMount} />;
     * }
     * ```
     */
    protected get onSlotMount(): (slotName: string, el: HTMLElement | null) => Promise<void>;
    /**
     * Converts data-* attributes to a props object.
     * Automatically attempts JSON parsing for rich values (numbers, booleans,
     * arrays, objects). Falls back to string if parsing fails.
     *
     * @returns Config object with parsed data attributes
     *
     * @example
     * ```html
     * <my-element data-count="5" data-enabled="true" data-items="[1,2,3]" data-title="Hello">
     * ```
     * Results in: { count: 5, enabled: true, items: [1,2,3], title: "Hello" }
     */
    protected getConfig(): Record<string, unknown>;
    /**
     * The namespace for Shiny module support, derived from the element's id.
     * Returns undefined if no id is set.
     */
    protected get namespace(): string | undefined;
    /**
     * Renders the React component. Override this to customize rendering,
     * pass additional props, or wrap in providers.
     *
     * @returns React node to render
     */
    protected render(): React.ReactNode;
    /**
     * Wraps content in ShinyModuleProvider if namespace exists.
     */
    private wrapWithProvider;
    /**
     * Clears the element's innerHTML before React renders.
     * Override with a no-op if you need to preserve existing content.
     */
    protected clearContent(): void;
    /**
     * Called when the element is added to the DOM.
     * Captures slots, clears content, and renders the React component.
     */
    connectedCallback(): void;
    /**
     * Called when the element is removed from the DOM.
     * Unbinds Shiny and unmounts the React root.
     */
    disconnectedCallback(): void;
}
