/**
 * Default flat-config fragment for Gate 0 of `auditing-typescript-tests`.
 *
 * Usage from the skill (Gate 0 invocation):
 *
 *   pnpm eslint \
 *     --config ${CLAUDE_SKILL_DIR}/eslint-rules/eslint.audit.config.ts \
 *     --format json \
 *     <spec-node>/tests/
 *
 * Consumer override: create `eslint.audit.config.ts` at the repo root that
 * re-exports this config with overrides. The skill resolves the consumer
 * override first and falls back to this default.
 *
 * Severities:
 *   "error" — fails Gate 0 (filename, literals, BDD try/catch, ad-hoc constants)
 *   "warn"  — informational, surfaces to Gate 1 (mock API detection)
 *
 * ESLint exits non-zero on errors only. The skill reads the JSON output to
 * extract both error- and warn-level findings.
 */

import tsParser from "@typescript-eslint/parser";

import auditPlugin from "./index";

const TEST_FILE_GLOBS = [
  "**/*.test.ts",
  "**/*.test.tsx",
  "**/*.spec.ts",
  "**/*.spec.tsx",
];

const config = [
  {
    files: TEST_FILE_GLOBS,
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2023,
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      audit: auditPlugin,
    },
    rules: {
      // Rejection rules — failing any of these fails Gate 0
      "audit/no-test-filename-violations": "error",
      "audit/no-literal-test-strings": "error",
      "audit/no-literal-test-numbers": "error",
      "audit/no-ad-hoc-test-constants": "error",
      "audit/no-bdd-try-catch-anti-pattern": "error",

      // Informational rule — Gate 1 consumes the warnings
      "audit/no-mock-api": "warn",

      // H1-H2: no deep relative imports into testing/
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["../../../**/testing/**", "../../../../**"],
              message:
                "Deep relative import. Use the `@testing/*` alias for shared test infrastructure or a co-located `./helpers` for single-test-file helpers.",
            },
          ],
        },
      ],
    },
  },
];

export default config;
