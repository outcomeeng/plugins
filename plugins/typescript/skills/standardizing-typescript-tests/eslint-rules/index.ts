/**
 * ESLint plugin for `auditing-typescript-tests` Gate 0 per-file checks.
 *
 * Rules:
 *   no-test-filename-violations — F1-F5 (canonical filename pattern)
 *   no-mock-api                 — M1-M2 (informational mock-API detection)
 *   no-literal-test-strings     — L1 (string literal discipline)
 *   no-literal-test-numbers     — L2 (numeric literal discipline)
 *   no-ad-hoc-test-constants    — module-scope constants backed by literal data
 *   no-bdd-try-catch-anti-pattern — expect() hidden in catch-swallowing blocks
 *
 * The companion cross-file check (literal-reuse across src/ and tests/) is
 * `spx validate literals`, not an ESLint rule — cross-file analysis doesn't
 * fit ESLint's per-file execution model.
 */

import noAdHocTestConstants from "./no-ad-hoc-test-constants";
import noBddTryCatchAntiPattern from "./no-bdd-try-catch-anti-pattern";
import noLiteralTestNumbers from "./no-literal-test-numbers";
import noLiteralTestStrings from "./no-literal-test-strings";
import noMockApi from "./no-mock-api";
import noTestFilenameViolations from "./no-test-filename-violations";

const plugin = {
  meta: {
    name: "eslint-plugin-auditing-typescript-tests",
    version: "0.1.0",
    namespace: "audit",
  },
  rules: {
    "no-ad-hoc-test-constants": noAdHocTestConstants,
    "no-bdd-try-catch-anti-pattern": noBddTryCatchAntiPattern,
    "no-literal-test-numbers": noLiteralTestNumbers,
    "no-literal-test-strings": noLiteralTestStrings,
    "no-mock-api": noMockApi,
    "no-test-filename-violations": noTestFilenameViolations,
  },
};

export default plugin;
