import { afterEach, describe, expect, it, vi } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";

import {
  PROTOCOL_VERSION,
  assertProtocolCompatible,
  readShinyReactConfig,
  throwVisibly,
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
  document.getElementById("shinyreact-fatal-error")?.remove();
  vi.restoreAllMocks();
});

function bannerText(): string | undefined {
  return document.getElementById("shinyreact-fatal-error")?.textContent ?? undefined;
}

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

describe("handshake failures are visible on the page", () => {
  it("shows a banner when the server major is newer", () => {
    expect(() => assertProtocolCompatible("999.0")).toThrow();
    expect(bannerText()).toContain("999.0");
    expect(bannerText()).toContain(PROTOCOL_VERSION);
  });

  it("shows a banner when the server major is older", () => {
    expect(() => assertProtocolCompatible("0.9")).toThrow();
    expect(bannerText()).toContain("0.9");
    expect(bannerText()).toContain(PROTOCOL_VERSION);
  });

  it("reuses one banner element across repeated failures", () => {
    expect(() => assertProtocolCompatible("999.0")).toThrow();
    expect(() => assertProtocolCompatible("998.0")).toThrow();
    expect(document.querySelectorAll("#shinyreact-fatal-error")).toHaveLength(1);
    expect(bannerText()).toContain("998.0");
  });

  it("renders backticked literals as <code> chips", () => {
    expect(() => assertProtocolCompatible("999.0")).toThrow();
    const chips = Array.from(
      document.querySelectorAll("#shinyreact-fatal-error code"),
    ).map((el) => el.textContent);
    expect(chips).toEqual(["999.0", PROTOCOL_VERSION]);
  });

  it("does not interpret the message as HTML", () => {
    expect(() => assertProtocolCompatible("<img src=x onerror=alert(1)>")).toThrow();
    const banner = document.getElementById("shinyreact-fatal-error");
    expect(banner?.querySelector("img")).toBeNull();
    expect(banner?.textContent).toContain("<img src=x onerror=alert(1)>");
  });

  it("strips the backticks from the thrown message", () => {
    expect(() => assertProtocolCompatible("999.0")).toThrowError(
      /server speaks protocol 999\.0 but/,
    );
  });

  it("still throws the same message it displays", () => {
    let thrown: Error | undefined;
    try {
      throwVisibly("boom");
    } catch (err) {
      thrown = err as Error;
    }
    expect(thrown?.message).toBe("boom");
    expect(bannerText()).toBe("boom");
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

describe("protocol fixture", () => {
  it("round-trips the shared wire-contract fixture", () => {
    // protocol/fixtures/config-restore.json is shared with the Python and R
    // suites (see protocol/README.md). Mirrors Python's
    // test_protocol_fixture_round_trips.
    let repoRoot = process.cwd();
    while (!existsSync(join(repoRoot, "protocol")) && dirname(repoRoot) !== repoRoot) {
      repoRoot = dirname(repoRoot);
    }
    const fixturePath = join(repoRoot, "protocol", "fixtures", "config-restore.json");
    if (!existsSync(fixturePath)) return; // monorepo sources not available
    const expected = JSON.parse(readFileSync(fixturePath, "utf8"));
    expect(expected.protocolVersion).toBe(PROTOCOL_VERSION);
    // Apply the server-side escaping rule (every "<" as backslash-u003c) when
    // emitting, exactly as the Python/R emitters do.
    setConfigTag(JSON.stringify(expected).replace(/</g, "\\u003c"));
    expect(readShinyReactConfig()).toEqual(expected);
  });
});
