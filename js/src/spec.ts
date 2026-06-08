import type { ComponentType, ReactNode } from "react";

/**
 * A node in the wire tree. `type` is a closed discriminant; `name` carries the
 * component name (`react`) or DOM tag name (`tag`). Mirrors the Python walker
 * output in `pkg-py/src/shinyreact/_spec.py`.
 */
export interface ComponentElement {
  type: "react";
  name: string;
  props: Record<string, unknown>;
  children?: Element[];
}

export interface TagElement {
  type: "tag";
  name: string;
  props: Record<string, unknown>;
  children?: Element[];
}

export interface TextElement {
  type: "text";
  value: string;
}

export interface HtmlElement {
  type: "html";
  html: string;
}

export type Element = ComponentElement | TagElement | TextElement | HtmlElement;

/**
 * The root payload rendered into a `.shinyreact-output` element: a single
 * node, or several sibling nodes (e.g. a Python `TagList`).
 */
export type Spec = Element | Element[];

/**
 * Props passed to registered React components. They receive the raw `react`
 * element plus already-rendered `children`, and read `element.props`.
 */
export interface RegisteredComponentProps {
  element: ComponentElement;
  children: ReactNode;
}

/**
 * Map of component name → React component. Populated by downstream packages
 * via `window.shinyreact.registerComponents()`.
 */
export type ComponentRegistry = Record<
  string,
  ComponentType<RegisteredComponentProps>
>;
