/**
 * Disallow raw numeric literals in test bodies outside the tiny allowed set.
 *
 * The default policy permits -1, 0, 1, 2 (structural constants — array
 * indices, small counters, boolean-like sentinels) and forces precision
 * matchers (`toBeCloseTo`) to carry a named precision argument.
 *
 * Every other number must come from a production import, a harness constant
 * (timeout, viewport, tolerance), or a seeded generator. Ad-hoc literals
 * mask the boundary conditions tests claim to exercise.
 */

import type { Rule } from "eslint";

import { TEST_NUMBER_POLICY } from "./config/test-number-policy";

type AstNode = {
  type: string;
  parent?: AstNode | null;
  [key: string]: unknown;
};

type CallArgumentContext = {
  readonly argumentIndex: number;
  readonly calleePropertyName: string | null;
};

const EXEMPT_SUFFIXES = [
  "eslint-rules/no-literal-test-numbers.ts",
  "eslint-rules/config/test-number-policy.ts",
] as const;

function isExemptFile(filename: string): boolean {
  return EXEMPT_SUFFIXES.some((suffix) => filename.endsWith(suffix));
}

function isNumericLiteral(node: AstNode | null | undefined): boolean {
  return node?.type === "Literal" && typeof node.value === "number";
}

function getCalleePropertyName(node: AstNode | null | undefined): string | null {
  if (!node) return null;
  if (node.type === "Identifier" && typeof node.name === "string") {
    return node.name;
  }
  if (
    node.type === "MemberExpression"
    && node.computed !== true
    && node.property
    && typeof node.property === "object"
  ) {
    return getCalleePropertyName(node.property as AstNode);
  }
  return null;
}

function getCallArgumentContext(node: AstNode): CallArgumentContext | null {
  let current: AstNode | null | undefined = node;

  while (current?.parent) {
    const parent: AstNode = current.parent;
    if (parent.type === "CallExpression" && Array.isArray(parent.arguments)) {
      const argumentIndex = parent.arguments.indexOf(current);
      if (argumentIndex >= 0) {
        return {
          argumentIndex,
          calleePropertyName: getCalleePropertyName(parent.callee as AstNode),
        };
      }
    }

    current = parent;
  }

  return null;
}

function requiresNamedCallsite(context: CallArgumentContext | null): boolean {
  if (!context) return false;

  return TEST_NUMBER_POLICY.alwaysNamedCallsites.some((callsite) => {
    return (
      context.argumentIndex === callsite.argumentIndex
      && context.calleePropertyName !== null
      && callsite.calleePropertyNames.some((name) => name === context.calleePropertyName)
    );
  });
}

function isAllowedRawNumber(value: number, context: CallArgumentContext | null): boolean {
  if (requiresNamedCallsite(context)) {
    return false;
  }

  return TEST_NUMBER_POLICY.allowedRawNumbers.some((allowedValue) => allowedValue === value);
}

const rule: Rule.RuleModule = {
  meta: {
    type: "problem",
    docs: {
      description: "Disallow raw numeric literals in tests outside the structural allowlist and policy exceptions",
    },
    messages: {
      literalTestNumber:
        "Raw numeric literal '{{value}}' in test code. Import product-owned values from the production module, protocol values from platform constants, and harness values (timeouts, viewports, tolerances) from shared test infrastructure.",
    },
  },

  create(context) {
    const filename = context.filename ?? context.getFilename();
    if (isExemptFile(filename)) return {};

    function reportIfNeeded(node: AstNode, value: number) {
      const callArgumentContext = getCallArgumentContext(node);
      if (isAllowedRawNumber(value, callArgumentContext)) {
        return;
      }

      context.report({
        node,
        messageId: "literalTestNumber",
        data: { value: String(value) },
      });
    }

    return {
      Literal(node) {
        if (typeof node.value !== "number") return;
        if (
          node.parent?.type === "UnaryExpression"
          && (node.parent.operator === "-" || node.parent.operator === "+")
        ) {
          return;
        }

        reportIfNeeded(node as unknown as AstNode, node.value);
      },
      UnaryExpression(node) {
        if (node.operator !== "-") return;

        const argument = node.argument as AstNode;
        if (!isNumericLiteral(argument)) return;

        reportIfNeeded(node as unknown as AstNode, -Number(argument.value));
      },
    };
  },
};

export default rule;
