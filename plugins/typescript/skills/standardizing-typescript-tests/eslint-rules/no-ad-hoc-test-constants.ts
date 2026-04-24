/**
 * Disallow module-scope ad hoc test constants backed by literal data.
 *
 * Inspects the initializer, not the name. `UPPER_SNAKE_CASE` renamed to
 * `fooBar` still carries the same literal data — the rule catches both.
 *
 * Scope (first slice):
 * - module-scope `const` declarations only
 * - direct string-backed initializers (literal, template, array, object)
 * - `as const` / `satisfies` wrappers unwrapped before inspection
 */

import type { Rule } from "eslint";

import { isMeaningfulString } from "./literal-signal";

type AstNode = {
  type: string;
  parent?: AstNode | null;
  [key: string]: unknown;
};

const EXEMPT_SUFFIXES = [
  "eslint-rules/no-ad-hoc-test-constants.ts",
  "eslint-rules/literal-signal.ts",
];

const CANDIDATE_INITIALIZER_TYPES = new Set([
  "Literal",
  "TemplateLiteral",
  "ArrayExpression",
  "ObjectExpression",
]);

function isExemptFile(filename: string): boolean {
  return EXEMPT_SUFFIXES.some((suffix) => filename.endsWith(suffix));
}

function unwrapTypeWrappers(node: AstNode | null | undefined): AstNode | null | undefined {
  let current = node;
  while (
    current
    && (
      current.type === "TSAsExpression"
      || current.type === "TSTypeAssertion"
      || current.type === "TSSatisfiesExpression"
    )
  ) {
    const next = current.expression;
    if (!next || typeof next !== "object") {
      return current;
    }
    current = next as AstNode;
  }
  return current;
}

function isModuleScopeConstDeclarator(node: AstNode): boolean {
  const declaration = node.parent;
  if (!declaration || declaration.type !== "VariableDeclaration") return false;
  if (declaration.kind !== "const") return false;

  const declarationParent = declaration.parent;
  if (!declarationParent) return false;
  if (declarationParent.type === "Program") return true;

  return (
    declarationParent.type === "ExportNamedDeclaration"
    && declarationParent.parent?.type === "Program"
  );
}

function containsMeaningfulLiteral(node: unknown): boolean {
  if (!node || typeof node !== "object") return false;
  const typed = node as AstNode;

  if (typed.type === "Literal") {
    if (typeof typed.value === "string") {
      return isMeaningfulString(typed.value);
    }
    return false;
  }

  if (typed.type === "TemplateElement") {
    const templateValue = typed.value;
    if (!templateValue || typeof templateValue !== "object") return false;
    const cooked = (templateValue as { cooked?: unknown }).cooked;
    return typeof cooked === "string" && isMeaningfulString(cooked);
  }

  for (const [key, child] of Object.entries(typed)) {
    if (key === "parent" || key === "loc" || key === "range") continue;
    if (Array.isArray(child)) {
      for (const item of child) {
        if (containsMeaningfulLiteral(item)) return true;
      }
      continue;
    }
    if (containsMeaningfulLiteral(child)) return true;
  }

  return false;
}

const rule: Rule.RuleModule = {
  meta: {
    type: "problem",
    docs: {
      description: "Disallow module-scope ad hoc test constants backed by literal data",
    },
    messages: {
      adHocTestConstant:
        "Module-scope test constant backed by literal data. Import owned values from the production module when they exist. Otherwise generate synthetic values through a test factory or PRNG helper — do not name a local literal constant.",
    },
  },

  create(context) {
    const filename = context.filename ?? context.getFilename();
    if (isExemptFile(filename)) return {};

    return {
      VariableDeclarator(node) {
        if (!isModuleScopeConstDeclarator(node as unknown as AstNode)) return;
        if (node.id.type !== "Identifier") return;

        const initializer = unwrapTypeWrappers(node.init as unknown as AstNode | null);
        if (!initializer) return;
        if (!CANDIDATE_INITIALIZER_TYPES.has(initializer.type)) return;
        if (!containsMeaningfulLiteral(initializer)) return;

        context.report({
          node,
          messageId: "adHocTestConstant",
        });
      },
    };
  },
};

export default rule;
