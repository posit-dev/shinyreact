import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { ShinyReactComponentElement } from "../ShinyReactComponentElement";

// Register the custom element so jsdom allows `new ShinyReactComponentElement()`
customElements.define("test-shiny-react-component", ShinyReactComponentElement);

// Minimal Shiny mock on window
beforeEach(() => {
  (window as any).Shiny = {
    bindAll: vi.fn(),
    unbindAll: vi.fn(),
  };
});

afterEach(() => {
  delete (window as any).Shiny;
});

describe("ShinyReactComponentElement", () => {
  describe("lifecycle", () => {
    it("mounts a React root on connect and unmounts it on disconnect", () => {
      const el = document.createElement(
        "test-shiny-react-component",
      ) as ShinyReactComponentElement;
      el.innerHTML = "<span>server content</span>";
      document.body.appendChild(el);

      // connectedCallback captured the slot content and cleared the element
      // before rendering, so the server markup is no longer a child.
      expect(el.querySelector("span")).toBeNull();
      expect((el as any).root).not.toBeNull();

      el.remove();

      expect((el as any).root).toBeNull();
    });

    it("unbinds Shiny on disconnect, WITHOUT includeSelf", () => {
      // Deliberately pinned as-is: ShinyOutput passes includeSelf=true so it
      // unbinds only itself, while this passes the element as a plain scope,
      // which unbinds descendants and leaves the element itself bound. The
      // asymmetry is unexplained (#223); this test documents today's behavior
      // so a change to it is a visible decision rather than a silent drift.
      const el = document.createElement("test-shiny-react-component");
      document.body.appendChild(el);
      el.remove();

      expect((window as any).Shiny.unbindAll).toHaveBeenCalledWith(el);
      expect((window as any).Shiny.unbindAll).not.toHaveBeenCalledWith(
        el,
        true,
      );
    });

    it("does not throw when Shiny is absent on disconnect", () => {
      delete (window as any).Shiny;
      const el = document.createElement("test-shiny-react-component");
      document.body.appendChild(el);

      expect(() => el.remove()).not.toThrow();
    });
  });

  describe("getConfig", () => {
    it("parses data-* attributes into a config object", () => {
      const el = new ShinyReactComponentElement();
      el.setAttribute("data-count", "5");
      el.setAttribute("data-title", "Hello");
      el.setAttribute("data-enabled", "true");
      el.setAttribute("data-items", "[1,2,3]");

      const config = (el as any).getConfig();

      expect(config.count).toBe(5);
      expect(config.title).toBe("Hello");
      expect(config.enabled).toBe(true);
      expect(config.items).toEqual([1, 2, 3]);
    });

    it("falls back to string for non-JSON values", () => {
      const el = new ShinyReactComponentElement();
      el.setAttribute("data-label", "not json");

      const config = (el as any).getConfig();
      expect(config.label).toBe("not json");
    });
  });

  describe("namespace", () => {
    it("returns undefined when no id is set", () => {
      const el = new ShinyReactComponentElement();
      expect((el as any).namespace).toBeUndefined();
    });

    it("returns the element id as namespace", () => {
      const el = new ShinyReactComponentElement();
      el.id = "counter1";
      expect((el as any).namespace).toBe("counter1");
    });
  });

  describe("captureSlots", () => {
    it("captures children as __children__ when no data-slot elements exist", () => {
      const el = new ShinyReactComponentElement();
      const child = document.createElement("div");
      child.textContent = "hello";
      el.appendChild(child);

      const slots = (el as any).captureSlots();
      expect(slots.has("__children__")).toBe(true);
      expect(slots.get("__children__")).toHaveLength(1);
    });

    it("captures named slots from data-slot attributes", () => {
      const el = new ShinyReactComponentElement();
      const sidebar = document.createElement("div");
      sidebar.setAttribute("data-slot", "sidebar");
      sidebar.innerHTML = "<p>Sidebar</p>";
      el.appendChild(sidebar);

      const main = document.createElement("div");
      main.setAttribute("data-slot", "main");
      main.innerHTML = "<p>Main</p>";
      el.appendChild(main);

      const slots = (el as any).captureSlots();
      expect(slots.has("sidebar")).toBe(true);
      expect(slots.has("main")).toBe(true);
      // No non-slotted children, so __children__ should be absent
      expect(slots.has("__children__")).toBe(false);
    });

    it("captures both named slots and remaining children as __children__", () => {
      const el = new ShinyReactComponentElement();

      const sidebar = document.createElement("div");
      sidebar.setAttribute("data-slot", "sidebar");
      sidebar.innerHTML = "<p>Sidebar</p>";
      el.appendChild(sidebar);

      const loose = document.createElement("p");
      loose.textContent = "Non-slotted content";
      el.appendChild(loose);

      const main = document.createElement("div");
      main.setAttribute("data-slot", "main");
      main.innerHTML = "<p>Main</p>";
      el.appendChild(main);

      const slots = (el as any).captureSlots();
      expect(slots.has("sidebar")).toBe(true);
      expect(slots.has("main")).toBe(true);
      expect(slots.has("__children__")).toBe(true);
      expect(slots.get("__children__")).toHaveLength(1);
      expect(slots.get("__children__")[0]).toBe(loose);
    });

    it("returns empty map when element has no children", () => {
      const el = new ShinyReactComponentElement();
      const slots = (el as any).captureSlots();
      expect(slots.size).toBe(0);
    });
  });

  describe("mountSlot", () => {
    it("moves captured content into a container and calls Shiny.bindAll", async () => {
      const el = new ShinyReactComponentElement();
      const child = document.createElement("div");
      child.textContent = "hello";
      el.appendChild(child);
      (el as any).captureSlots();

      const container = document.createElement("div");
      await (el as any).mountSlot("__children__", container);

      expect(container.childNodes).toHaveLength(1);
      expect(container.textContent).toBe("hello");
      expect((window as any).Shiny.bindAll).toHaveBeenCalledWith(container);
    });

    it("does nothing when slot name not found", async () => {
      const el = new ShinyReactComponentElement();
      const container = document.createElement("div");
      await (el as any).mountSlot("nonexistent", container);
      expect(container.childNodes).toHaveLength(0);
    });
  });
});
