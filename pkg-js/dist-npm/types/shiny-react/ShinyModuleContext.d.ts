import { type ReactNode } from "react";
export interface ShinyModuleProviderProps {
    namespace: string;
    children: ReactNode;
}
/**
 * Provides a namespace context for Shiny module support.
 *
 * All child components using useShinyInput, useShinyOutput, or
 * useShinyMessageHandler will automatically have their IDs prefixed
 * with the provided namespace.
 *
 * Note: Nesting providers is supported — an inner provider overrides the
 * outer one (it does not concatenate namespaces). If you need a combined
 * namespace, pass the full string (e.g., "outer-inner") directly.
 *
 * @param namespace The complete namespace string to apply to child hooks.
 * @param children React children that will receive the namespace context.
 *
 * @example
 * ```tsx
 * <ShinyModuleProvider namespace="myModule">
 *   <MyComponent />
 * </ShinyModuleProvider>
 * ```
 */
export declare function ShinyModuleProvider({ namespace, children, }: ShinyModuleProviderProps): import("react/jsx-runtime").JSX.Element;
/**
 * Hook to access the current module namespace from context.
 * Returns null if not within a ShinyModuleProvider.
 */
export declare function useShinyModuleNamespace(): string | null;
/**
 * Utility function to apply namespace to an ID.
 * If namespace is a non-empty string, returns `${namespace}-${id}`.
 * If namespace is null, undefined, or empty string, returns the original id.
 */
export declare function applyNamespace(id: string, namespace: string | null): string;
/**
 * Hook: resolve `id` against the provider context and an optional explicit
 * override, then return the namespaced id.
 *
 * Precedence: an explicit value (including `null`) wins over the provider
 * context. `undefined` falls through to the context.
 *
 * - `explicit === undefined`: use the surrounding `ShinyModuleProvider`
 *   namespace, or no prefix if there isn't one.
 * - `explicit === "ns"`: prefix with `"ns-"`, ignoring any provider.
 * - `explicit === null`: opt out — render the bare `id`. Useful when `id`
 *   already contains a prefix (e.g. ImageOutput's clientdata IDs).
 *
 * Centralising this here keeps `null` from being conflated with `undefined`
 * (a `??` would silently fall through to the context).
 */
export declare function useNamespacedId(id: string, explicit: string | null | undefined): string;
