import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { installGlobal } from "../global";

/**
 * The `shinyreact-build-app` skill teaches the `window.shinyreact` surface, so
 * adding an export without teaching it leaves agents building apps against a
 * stale API — the staleness mode a skill cannot self-detect, because prose
 * stays syntactically valid forever.
 *
 * This pins the one part that is mechanically checkable: every published name
 * is either taught by the skill or listed below as a deliberate omission. A new
 * export fails here until someone decides which it is.
 *
 * See .claude/references/writing-skills.md for the rest of the update loop,
 * which is a reflex rather than a test.
 */
const REPO_ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../..",
);
const SKILL = path.join(
  REPO_ROOT,
  ".claude/skills/shinyreact-build-app/SKILL.md",
);

// Names the skill deliberately does not teach, with why. Shrinking this list is
// an improvement; growing it needs a reason.
const NOT_TAUGHT: Record<string, string> = {
  MISSING: "an output-registry sentinel app authors never construct",
  ShinyReactComponentElement:
    "the custom-element base class, for component authors rather than app authors",
};

describe("shinyreact-build-app skill", () => {
  it("teaches every name on window.shinyreact", () => {
    installGlobal();
    const source = fs.readFileSync(SKILL, "utf-8");

    const untaught = Object.keys(window.shinyreact)
      .filter((name) => !(name in NOT_TAUGHT))
      .filter((name) => !new RegExp(`\\b${name}\\b`).test(source));

    expect(untaught).toEqual([]);
  });

  it("does not list omitted names in NOT_TAUGHT once they are gone", () => {
    installGlobal();
    const published = new Set(Object.keys(window.shinyreact));

    expect(
      Object.keys(NOT_TAUGHT).filter((name) => !published.has(name)),
    ).toEqual([]);
  });
});
