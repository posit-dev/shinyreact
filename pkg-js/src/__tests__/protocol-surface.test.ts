import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { PROTOCOL_VERSION } from "../shiny-react/config";

/**
 * Guards the client/server boundary surface against silent growth.
 *
 * `protocol/surface.json` lists every name that crosses the boundary, next to
 * the protocol version that describes it. This test scans the JS source and
 * fails when it finds a custom-message type, a `:type` handler suffix, or a
 * shinyreact input id that the manifest does not list.
 *
 * Why a source scan rather than a runtime assertion: a type only observable
 * when Shiny is present and a message arrives is exactly the kind of thing a
 * unit test misses. The literal in the source is the thing that matters.
 *
 * This exists because the surface already grew unnoticed: #221 added
 * `shinyreact.init` and `shinyreact-deps` while all three protocol constants
 * still documented "exactly three" boundary shapes (posit-dev/shinyreact#232).
 */

const repoRoot = join(__dirname, "..", "..", "..");
const manifest = JSON.parse(
  readFileSync(join(repoRoot, "protocol", "surface.json"), "utf8"),
) as {
  protocolVersion: string;
  customMessages: Record<string, string>;
  inputHandlers: Record<string, string>;
  inputIds: Record<string, string>;
  domIds: Record<string, string>;
};

/** Every .ts/.tsx under pkg-js/src, excluding tests. */
function sourceFiles(): string[] {
  const out: string[] = [];
  const walk = (dir: string): void => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name !== "__tests__" && entry.name !== "node_modules") {
          walk(path);
        }
      } else if (/\.tsx?$/.test(entry.name)) {
        out.push(path);
      }
    }
  };
  walk(join(repoRoot, "pkg-js", "src"));
  return out;
}


const sources = sourceFiles().map((f) => readFileSync(f, "utf8"));
const allSource = sources.join("\n");

function matchAll(re: RegExp): string[] {
  return [...new Set([...allSource.matchAll(re)].map((m) => m[1]))].sort();
}

describe("protocol surface (pkg-js/src vs protocol/surface.json)", () => {
  it("scans a non-trivial number of source files", () => {
    // Guard against the walk silently finding nothing and every assertion
    // below passing vacuously.
    expect(sources.length).toBeGreaterThan(10);
  });

  it("registers no custom message type the manifest does not list", () => {
    const found = matchAll(/addCustomMessageHandler\(\s*["'`]([^"'`]+)["'`]/g);
    expect(found).toEqual(
      Object.keys(manifest.customMessages).filter((m) => found.includes(m)),
    );
    for (const type of found) {
      expect(
        Object.keys(manifest.customMessages),
        `custom message "${type}" is not in protocol/surface.json — add it there and decide whether the protocol version must change (#232)`,
      ).toContain(type);
    }
  });

  it("sends no input id or handler type the manifest does not list", () => {
    // Matches the wire form the hooks and dep-discovery use: `id:type`.
    const wireIds = matchAll(/setInputValue\?*\(\s*["'`]([^"'`]+)["'`]/g);
    for (const wireId of wireIds) {
      const [id, type] = wireId.split(":");
      expect(
        Object.keys(manifest.inputIds),
        `input id "${id}" is not in protocol/surface.json (#232)`,
      ).toContain(id);
      if (type !== undefined) {
        expect(
          Object.keys(manifest.inputHandlers),
          `handler type "${type}" is not in protocol/surface.json (#232)`,
        ).toContain(type);
      }
    }
  });

  it("uses the manifest's default handler name as the untyped suffix", () => {
    // The hook appends this to every untyped input id, so it is the most
    // load-bearing name on the wire.
    expect(allSource).toContain('DEFAULT_TYPE = "shinyreact.default"');
    expect(Object.keys(manifest.inputHandlers)).toContain("shinyreact.default");
  });

  it("reads the config tag by the manifest's id", () => {
    const found = matchAll(/getElementById\(\s*["'`]([^"'`]+)["'`]/g);
    for (const id of found) {
      expect(Object.keys(manifest.domIds)).toContain(id);
    }
  });

  it("declares the manifest's protocol version", () => {
    expect(PROTOCOL_VERSION).toBe(manifest.protocolVersion);
  });
});
