/**
 * Level 1 conformance tests for `no-literal-test-strings`.
 *
 * Evidence: RuleTester drives ESLint's real rule engine against the rule
 * module imported via `@eslint-rules/*`. No mocking, no filesystem. Pure
 * AST-in / report-out computation.
 */

import rule from "@eslint-rules/no-literal-test-strings";
import tsParser from "@typescript-eslint/parser";
import { RuleTester } from "eslint";
import { describe, it } from "vitest";

RuleTester.describe = describe;
RuleTester.it = it;
RuleTester.itOnly = it.only;

const ruleTester = new RuleTester({
  languageOptions: {
    parser: tsParser,
    parserOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      ecmaFeatures: { jsx: true },
    },
  },
});

ruleTester.run("no-literal-test-strings", rule, {
  valid: [
    // Direct identifier callee — it / describe / test
    { code: `it("runs the happy path", () => {});` },
    { code: `describe("outer suite scope", () => {});` },
    { code: `test("runs the happy path", () => {});` },

    // Member-expression modifiers on the direct form
    { code: `it.skip("disabled for now", () => {});` },
    { code: `it.only("focus this case please", () => {});` },
    { code: `it.todo("someday maybe");` },
    { code: `test.skip("disabled for now", () => {});` },
    { code: `test.only("focus this case please", () => {});` },
    { code: `test.todo("someday maybe");` },

    // Curried .each — the title literal lives on the outer call
    { code: `it.each(CASES)("handles %s input", (arg) => {});` },
    { code: `test.each(CASES)("checks %s value", (arg) => {});` },
    {
      code: `describe.each(TABLE)("group %s", () => { it("works as expected", () => {}); });`,
    },

    // Curried .each with a template-literal title
    { code: "it.each(CASES)(`template title ${x}`, (arg) => {});" },

    // Playwright test.describe / test.step
    { code: `test.describe("outer playwright group", () => {});` },
    { code: `test.step("inner step description", () => {});` },

    // expect assertion message — argumentIndex 1
    { code: `expect(value, "because the cart should be empty").toBe(other);` },

    // Protocol exceptions — one per category
    { code: `screen.getByRole("button");` },
    { code: `page.waitForLoadState("networkidle");` },
    { code: `element.getAttribute("href");` },
    { code: `element.hasAttribute("aria-label");` },
  ],

  invalid: [
    // Curried .each with a literal at argumentIndex 1 is NOT a title
    {
      code: `it.each(CASES)(fn, "extra-string-arg");`,
      errors: [{ messageId: "literalTestString" }],
    },

    // Unknown `.each` host does not match any policy entry
    {
      code: `myCustom.each(CASES)("custom runner title", fn);`,
      errors: [{ messageId: "literalTestString" }],
    },

    // Regression: the curried-each fix must not over-permit. A literal inside
    // an expect(...).toBe(...) call is still a magic value.
    {
      code: `it.each(CASES)("alpha case", () => { expect(result).toBe("magic-literal"); });`,
      errors: [{ messageId: "literalTestString" }],
    },

    // Ad-hoc literal in a module-scope const used as a curried-each title.
    // Only the `"magic-word"` literal is this rule's concern; the identifier
    // `X` passed as the title is not a literal and therefore not visited.
    {
      code: `const X = "magic-word"; it.each(CASES)(X, fn);`,
      errors: [{ messageId: "literalTestString" }],
    },

    // Classic ad-hoc literal reused in the assertion body
    {
      code: `const PATH = "/tmp/foo-bar"; it("writes the config", () => { expect(PATH).toBe("/tmp/foo-bar"); });`,
      errors: [
        { messageId: "literalTestString" },
        { messageId: "literalTestString" },
      ],
    },

    // Edge: a literal nested inside the curried-each body must still report.
    // The outer "outer title" at argumentIndex 0 is descriptive and must NOT
    // report — only `"leak-me-now"` is flagged.
    {
      code: `it.each(CASES)("outer title", () => { const ok = "leak-me-now"; });`,
      errors: [{ messageId: "literalTestString" }],
    },

    // Edge: computed member expression `it["each"]` is NOT recognised as
    // `.each`, so the curried title is flagged. The literal `"each"` inside
    // the computed member expression is also flagged (a separate concern of
    // the same rule — it's a meaningful literal outside a descriptive
    // callsite).
    {
      code: `it["each"](CASES)("dynamic title string", fn);`,
      errors: [
        { messageId: "literalTestString" },
        { messageId: "literalTestString" },
      ],
    },

    // The policy does not list `.concurrent.each` variants, so they report.
    {
      code: `describe.concurrent.each(CASES)("concurrent group title", fn);`,
      errors: [{ messageId: "literalTestString" }],
    },
  ],
});
