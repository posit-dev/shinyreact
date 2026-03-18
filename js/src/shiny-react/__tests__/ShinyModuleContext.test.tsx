import { describe, expect, it } from "vitest";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import {
  applyNamespace,
  ShinyModuleProvider,
  useShinyModuleNamespace,
} from "../ShinyModuleContext";

describe("applyNamespace", () => {
  it("prefixes id with namespace when namespace is provided", () => {
    expect(applyNamespace("count", "mod1")).toBe("mod1-count");
  });

  it("returns raw id when namespace is null", () => {
    expect(applyNamespace("count", null)).toBe("count");
  });

  it("returns raw id when namespace is empty string", () => {
    expect(applyNamespace("count", "")).toBe("count");
  });
});

describe("ShinyModuleProvider / useShinyModuleNamespace", () => {
  it("returns null when not inside a provider", () => {
    const { result } = renderHook(() => useShinyModuleNamespace());
    expect(result.current).toBeNull();
  });

  it("returns the namespace from the provider", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="myModule">{children}</ShinyModuleProvider>
    );
    const { result } = renderHook(() => useShinyModuleNamespace(), { wrapper });
    expect(result.current).toBe("myModule");
  });

  it("inner provider overrides outer provider", () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ShinyModuleProvider namespace="outer">
        <ShinyModuleProvider namespace="inner">{children}</ShinyModuleProvider>
      </ShinyModuleProvider>
    );
    const { result } = renderHook(() => useShinyModuleNamespace(), { wrapper });
    expect(result.current).toBe("inner");
  });
});
