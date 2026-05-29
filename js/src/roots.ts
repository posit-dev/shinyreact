import { createRoot, type Root } from "react-dom/client";

// One React root per output DOM element.
const roots = new WeakMap<Element, Root>();

export function getOrCreateRoot(el: HTMLElement): Root {
  let root = roots.get(el);
  if (!root) {
    root = createRoot(el);
    roots.set(el, root);
  }
  return root;
}

export function hasRoot(el: Element): boolean {
  return roots.has(el);
}

export function unmountRoot(el: Element): void {
  const root = roots.get(el);
  if (root) {
    root.unmount();
    roots.delete(el);
  }
}
