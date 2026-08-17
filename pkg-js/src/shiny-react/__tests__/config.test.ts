import { afterEach, describe, expect, it, vi } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";

import {
  PROTOCOL_VERSION,
  assertProtocolCompatible,
  readShinyReactConfig,
} from "../config";

function setConfigTag(text: string): void {
  const el = document.createElement("script");
  el.type = "application/json";
  el.id = "shinyreact-config";
  el.textContent = text;
  document.head.appendChild(el);
}

afterEach(() => {
  document.getElementById("shinyreact-config")?.remove();
  vi.restoreAllMocks();
});

describe("readShinyReactConfig", () => {
  it("returns null when the tag is absent", () => {
    expect(readShinyReactConfig()).toBeNull();
  });

  it("parses the tag payload", () => {
    setConfigTag('{"protocolVersion":"1.0","restore":{"foo":"hello"}}');
    expect(readShinyReactConfig()).toEqual({
      protocolVersion: "1.0",
      restore: { foo: "hello" },
    });
  });

  it("decodes \\u003c escapes the server uses to neutralize '<'", () => {
    setConfigTag('{"protocolVersion":"1.0","restore":{"foo":"\\u003c/script>"}}');
    expect(readShinyReactConfig()?.restore).toEqual({ foo: "</script>" });
  });

  it("logs and returns null on malformed JSON instead of throwing", () => {
    const err = vi.spyOn(console, "error").mockImplementation(() => {});
    setConfigTag("{not json");
    expect(readShinyReactConfig()).toBeNull();
    expect(err).toHaveBeenCalled();
  });
});

describe("assertProtocolCompatible", () => {
  it("accepts the same major version", () => {
    const major = PROTOCOL_VERSION.split(".")[0];
    expect(() => assertProtocolCompatible(`${major}.999`)).not.toThrow();
  });

  it("throws on a different major version, naming both versions", () => {
    expect(() => assertProtocolCompatible("999.0")).toThrowError(
      new RegExp(`999\\.0[\\s\\S]*${PROTOCOL_VERSION.replace(".", "\\.")}`),
    );
  });
});

describe("PROTOCOL_VERSION parity", () => {
  it("matches the Python and R declarations", () => {
    // PROTOCOL_VERSION is one contract declared in three languages; this
    // parity test pins all three to the same string. Mirrors Python's
    // test_protocol_version_matches_js_and_r and R's "protocol version
    // matches the JS and Python declarations".
    let repoRoot = process.cwd();
    while (!existsSync(join(repoRoot, "pkg-py")) && dirname(repoRoot) !== repoRoot) {
      repoRoot = dirname(repoRoot);
    }
    const pySrc = join(repoRoot, "pkg-py", "src", "shinyreact", "_protocol.py");
    const rSrc = join(repoRoot, "pkg-r", "R", "protocol.R");
    if (!existsSync(pySrc) || !existsSync(rSrc)) {
      // Monorepo sources not available — nothing to compare against.
      return;
    }
    const pyMatch = readFileSync(pySrc, "utf8").match(
      /PROTOCOL_VERSION = "([^"]+)"/,
    );
    const rMatch = readFileSync(rSrc, "utf8").match(
      /\.protocol_version <- "([^"]+)"/,
    );
    expect(pyMatch?.[1]).toBe(PROTOCOL_VERSION);
    expect(rMatch?.[1]).toBe(PROTOCOL_VERSION);
  });
});
