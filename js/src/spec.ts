import type { ComponentType, ReactNode } from "react";

/**
 * A single node in a Spec. `children` is a list of element IDs (strings) that
 * reference other entries in the parent Spec's `elements` map.
 *
 * Mirrors the Python dataclass in `pkg-py/src/shinyjsonold/_spec.py`.
 */
export interface Element {
  type: string;
  props: Record<string, unknown>;
  children?: string[];
}

/**
 * A flat map of element IDs to `Element` nodes, plus a `root` ID that
 * identifies the entry point for rendering.
 */
export interface Spec {
  root: string;
  elements: Record<string, Element>;
}

/**
 * Props passed to registered React components.
 *
 * Registered components receive the raw `Element` plus already-rendered
 * `children`. They are responsible for reading `element.props` themselves.
 *
 * Intrinsic HTML tags (e.g. `"div"`, `"span"`) are NOT registered components;
 * the renderer creates them with `element.props` spread directly.
 */
export interface RegisteredComponentProps {
  element: Element;
  children: ReactNode;
}

/**
 * Map of component name → React component. Populated by downstream packages
 * via `window.shinyjson.registerComponents()`.
 */
export type ComponentRegistry = Record<
  string,
  ComponentType<RegisteredComponentProps>
>;
