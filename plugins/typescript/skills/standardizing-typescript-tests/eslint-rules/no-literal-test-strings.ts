/**
 * Ban meaningful string literals in test bodies outside permitted contexts.
 *
 * Literals are allowed in: test descriptions (`it`/`describe`/`test` first
 * arg, including `.each`/`.skip`/`.todo`/`.only` variants), assertion messages
 * (`expect(value, "because X")`), and external-protocol values defined in the
 * policy (ARIA roles, Playwright load states, DOM attribute names).
 *
 * Everywhere else in a test file, literals must come from a production import
 * or a seeded generator. This prevents magic values from hiding in test bodies
 * where they mask bugs (a user id of `"admin"` routes through a privileged
 * branch that real users never hit).
 */

import type { Rule } from "eslint";

import { TEST_STRING_POLICY } from "./config/test-string-policy";
import { isMeaningfulString } from "./literal-signal";

type AstNode = {
  type: string;
  parent?: AstNode | null;
  [key: string]: unknown;
};

const EXEMPT_SUFFIXES = [
  "eslint-rules/no-literal-test-strings.ts",
  "eslint-rules/config/test-string-policy.ts",
  "eslint-rules/literal-signal.ts",
];

const SKIP_FIELD_BY_PARENT: ReadonlyMap<string, ReadonlySet<string>> = new Map([
  ["ImportDeclaration", new Set(["source"])],
  ["ImportExpression", new Set(["source"])],
  ["ExportNamedDeclaration", new Set(["source"])],
  ["ExportAllDeclaration", new Set(["source"])],
]);

function isExemptFile(filename: string): boolean {
  return EXEMPT_SUFFIXES.some((suffix) => filename.endsWith(suffix));
}

function getDirectStringValue(node: AstNode): string | null {
  if (node.type === "Literal" && typeof node.value === "string") {
    return node.value;
  }

  if (node.type === "TemplateLiteral") {
    const expressions = Array.isArray(node.expressions) ? node.expressions : [];
    if (expressions.length > 0) return null;

    const quasis = Array.isArray(node.quasis) ? node.quasis : [];
    return quasis
      .map((quasi) => {
        if (!quasi || typeof quasi !== "object") return "";
        const value = (quasi as AstNode).value;
        if (!value || typeof value !== "object") return "";
        const cooked = (value as { cooked?: unknown }).cooked;
        return typeof cooked === "string" ? cooked : "";
      })
      .join("");
  }

  return null;
}

function getTemplateLiteralSignal(node: AstNode): string[] {
  if (node.type !== "TemplateLiteral") return [];
  const quasis = Array.isArray(node.quasis) ? node.quasis : [];
  return quasis
    .map((quasi) => {
      if (!quasi || typeof quasi !== "object") return "";
      const value = (quasi as AstNode).value;
      if (!value || typeof value !== "object") return "";
      const cooked = (value as { cooked?: unknown }).cooked;
      return typeof cooked === "string" ? cooked : "";
    })
    .filter((text) => isMeaningfulString(text));
}

function getCallExpression(node: AstNode): AstNode | null {
  if (node.parent?.type === "CallExpression") {
    return node.parent;
  }

  if (node.parent?.type === "TemplateLiteral" && node.parent.parent?.type === "CallExpression") {
    return node.parent.parent;
  }

  return null;
}

function getArgumentIndex(callExpression: AstNode, node: AstNode): number {
  const directArguments = callExpression.arguments;
  if (!Array.isArray(directArguments)) return -1;

  const directIndex = directArguments.indexOf(node);
  if (directIndex >= 0) return directIndex;

  if (node.parent?.type === "TemplateLiteral") {
    return directArguments.indexOf(node.parent);
  }

  return -1;
}

function getCalleePath(node: AstNode | null | undefined): string | null {
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
    const objectPath = getCalleePath(node.object as AstNode);
    const propertyPath = getCalleePath(node.property as AstNode);
    if (objectPath && propertyPath) {
      return `${objectPath}.${propertyPath}`;
    }
  }

  return null;
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

function isDescriptiveCallsite(node: AstNode): boolean {
  const callExpression = getCallExpression(node);
  if (!callExpression) return false;

  const argumentIndex = getArgumentIndex(callExpression, node);
  if (argumentIndex < 0) return false;

  const callee = callExpression.callee as AstNode | undefined;
  if (!callee) return false;

  const directPath = getCalleePath(callee);
  if (directPath) {
    return TEST_STRING_POLICY.descriptiveCallsites.some((callsite) => {
      return callsite.callee === directPath && callsite.argumentIndex === argumentIndex;
    });
  }

  // Curried form: `it.each(cases)(title, fn)` and variants. The outer call's
  // callee is the `CallExpression` returned by `it.each(...)`; its inner
  // callee path ends in `.each`. The title argument lives on the outer call.
  if (callee.type === "CallExpression") {
    const innerPath = getCalleePath((callee as AstNode).callee as AstNode);
    if (innerPath && innerPath.endsWith(".each")) {
      return TEST_STRING_POLICY.descriptiveCallsites.some((callsite) => {
        return callsite.callee === innerPath && callsite.argumentIndex === argumentIndex;
      });
    }
  }

  return false;
}

function isProtocolException(node: AstNode, value: string): boolean {
  const callExpression = getCallExpression(node);
  if (!callExpression) return false;

  const argumentIndex = getArgumentIndex(callExpression, node);
  if (argumentIndex < 0) return false;

  const calleePropertyName = getCalleePropertyName(callExpression.callee as AstNode);
  if (!calleePropertyName) return false;

  return TEST_STRING_POLICY.protocolStringExceptions.some((exception) => {
    return (
      exception.argumentIndex === argumentIndex
      && exception.calleePropertyNames.includes(calleePropertyName)
      && exception.values.includes(value)
    );
  });
}

function isSkippedByParentField(node: AstNode): boolean {
  const parent = node.parent;
  if (!parent) return false;

  const skipFields = SKIP_FIELD_BY_PARENT.get(parent.type);
  if (!skipFields) return false;

  return [...skipFields].some((field) => {
    const child = parent[field];
    if (Array.isArray(child)) {
      return child.includes(node);
    }
    return child === node;
  });
}

function shouldReport(node: AstNode): boolean {
  if (isSkippedByParentField(node)) return false;
  if (isDescriptiveCallsite(node)) return false;

  const directValue = getDirectStringValue(node);
  if (directValue !== null) {
    if (!isMeaningfulString(directValue)) return false;
    if (isProtocolException(node, directValue)) return false;
    return true;
  }

  const templateSignals = getTemplateLiteralSignal(node);
  if (templateSignals.length === 0) return false;

  return templateSignals.every((signal) => !isProtocolException(node, signal));
}

const rule: Rule.RuleModule = {
  meta: {
    type: "problem",
    docs: {
      description: "Ban meaningful string literals in tests outside descriptive contexts and policy exceptions",
    },
    messages: {
      literalTestString:
        "Meaningful string literal in a test outside descriptive callsites. Move explanatory text into the test title or expect message, import source-owned values, or extend the policy `protocolStringExceptions` when the string is protocol-level.",
    },
  },

  create(context) {
    const filename = context.filename ?? context.getFilename();
    if (isExemptFile(filename)) return {};

    return {
      Literal(node) {
        if (typeof node.value !== "string") return;
        if (!shouldReport(node as unknown as AstNode)) return;

        context.report({
          node,
          messageId: "literalTestString",
        });
      },
      TemplateLiteral(node) {
        if (!shouldReport(node as unknown as AstNode)) return;

        context.report({
          node,
          messageId: "literalTestString",
        });
      },
    };
  },
};

export default rule;
