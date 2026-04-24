/**
 * Enforce the canonical test filename pattern.
 *
 * Required shape:  <subject>.<evidence>.<level>[.<runner>].test.ts
 *
 * Checks:
 *   F1 — filename matches the canonical pattern
 *   F2 — legacy suffixes rejected (.unit., .integration., .e2e., .spec.)
 *   F3 — evidence token is one of the five allowed values
 *   F4 — level token is l1, l2, or l3
 *   F5 — `.playwright.` runner token presence matches the file's import graph
 *         (present iff the file imports from `@playwright/test`)
 *
 * Legacy suffixes encode evidence/level ambiguously and cannot be auto-mapped
 * — the author must pick an evidence type and a level explicitly.
 */

import type { Rule } from "eslint";
import { basename } from "node:path";

const EVIDENCE_TOKENS = ["scenario", "mapping", "conformance", "property", "compliance"] as const;
const LEVEL_TOKENS = ["l1", "l2", "l3"] as const;

const LEGACY_SUFFIXES = [
  ".unit.test.ts",
  ".unit.test.tsx",
  ".integration.test.ts",
  ".integration.test.tsx",
  ".e2e.test.ts",
  ".e2e.test.tsx",
  ".spec.ts",
  ".spec.tsx",
] as const;

const PLAYWRIGHT_IMPORT_SPECIFIERS: ReadonlySet<string> = new Set([
  "@playwright/test",
  "playwright",
  "playwright/test",
  "playwright-core",
]);

type FilenameCheckResult =
  | { kind: "ok"; isPlaywright: boolean }
  | { kind: "legacy"; suffix: string }
  | { kind: "bad-shape"; reason: string }
  | { kind: "bad-evidence"; token: string }
  | { kind: "bad-level"; token: string };

function checkFilename(filename: string): FilenameCheckResult {
  const base = basename(filename);

  for (const suffix of LEGACY_SUFFIXES) {
    if (base.endsWith(suffix)) {
      return { kind: "legacy", suffix };
    }
  }

  if (!base.endsWith(".test.ts") && !base.endsWith(".test.tsx")) {
    return { kind: "bad-shape", reason: "file does not end in .test.ts or .test.tsx" };
  }

  const stem = base.replace(/\.test\.tsx?$/, "");
  const parts = stem.split(".");

  if (parts.length < 3) {
    return {
      kind: "bad-shape",
      reason: "expected <subject>.<evidence>.<level>[.<runner>].test.ts — at least 3 dot-separated tokens required",
    };
  }

  const runner = parts.length >= 4 ? parts[parts.length - 1] : null;
  const level = runner !== null ? parts[parts.length - 2] : parts[parts.length - 1];
  const evidence = runner !== null ? parts[parts.length - 3] : parts[parts.length - 2];

  if (!(EVIDENCE_TOKENS as readonly string[]).includes(evidence)) {
    return { kind: "bad-evidence", token: evidence };
  }

  if (!(LEVEL_TOKENS as readonly string[]).includes(level)) {
    return { kind: "bad-level", token: level };
  }

  return { kind: "ok", isPlaywright: runner === "playwright" };
}

const rule: Rule.RuleModule = {
  meta: {
    type: "problem",
    docs: {
      description: "Enforce canonical <subject>.<evidence>.<level>[.<runner>].test.ts filename pattern",
    },
    messages: {
      legacySuffix:
        "Legacy test filename suffix `{{suffix}}`. Rename to `<subject>.<evidence>.<level>[.<runner>].test.ts` where evidence ∈ {scenario, mapping, conformance, property, compliance} and level ∈ {l1, l2, l3}.",
      badShape: "Test filename does not match `<subject>.<evidence>.<level>[.<runner>].test.ts`: {{reason}}.",
      badEvidence:
        "Unknown evidence token `{{token}}`. Must be one of: scenario, mapping, conformance, property, compliance.",
      badLevel: "Unknown level token `{{token}}`. Must be one of: l1, l2, l3.",
      playwrightTokenMissing:
        "File imports from @playwright/test but filename lacks the `.playwright.` runner token. Rename to `<subject>.<evidence>.<level>.playwright.test.ts`.",
      playwrightTokenSpurious:
        "Filename carries the `.playwright.` runner token but the file does not import from @playwright/test. Remove the `.playwright.` token or add the Playwright import.",
    },
  },

  create(context) {
    const filename = context.filename ?? context.getFilename();
    const base = basename(filename);

    if (!/\.test\.tsx?$/.test(base) && !base.endsWith(".spec.ts") && !base.endsWith(".spec.tsx")) {
      return {};
    }

    const filenameResult = checkFilename(filename);

    let importsPlaywright = false;

    return {
      ImportDeclaration(node) {
        if (typeof node.source.value === "string" && PLAYWRIGHT_IMPORT_SPECIFIERS.has(node.source.value)) {
          importsPlaywright = true;
        }
      },
      "Program:exit"(node) {
        switch (filenameResult.kind) {
          case "legacy":
            context.report({
              node,
              messageId: "legacySuffix",
              data: { suffix: filenameResult.suffix },
            });
            return;
          case "bad-shape":
            context.report({
              node,
              messageId: "badShape",
              data: { reason: filenameResult.reason },
            });
            return;
          case "bad-evidence":
            context.report({
              node,
              messageId: "badEvidence",
              data: { token: filenameResult.token },
            });
            return;
          case "bad-level":
            context.report({
              node,
              messageId: "badLevel",
              data: { token: filenameResult.token },
            });
            return;
          case "ok":
            if (importsPlaywright && !filenameResult.isPlaywright) {
              context.report({ node, messageId: "playwrightTokenMissing" });
            } else if (!importsPlaywright && filenameResult.isPlaywright) {
              context.report({ node, messageId: "playwrightTokenSpurious" });
            }
            return;
        }
      },
    };
  },
};

export default rule;
