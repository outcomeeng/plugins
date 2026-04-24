/**
 * Detect mock / stub API call sites for Gate 1 consumption.
 *
 * This rule is INFORMATIONAL — it surfaces mock-API presence so the LLM at
 * Gate 1 (step "mocks") can judge each call site against the `/testing`
 * exception catalog (1: failure modes, 2: interaction protocols, 3:
 * time/concurrency, 4: safety, 5: combinatorial cost, 6: observability,
 * 7: contract testing).
 *
 * Configure severity `"warn"` in the audit config. ESLint exits 0 on warnings
 * only, so these findings do not reject Gate 0 — they populate the JSON
 * output the skill reads before invoking Gate 1.
 *
 * Detected API call sites:
 *   M1-vitest  — vi.mock, vi.doMock, vi.importMock, vi.hoisted-with-mock,
 *                vi.stubGlobal, vi.stubEnv, vi.spyOn(...).mockReturnValue,
 *                vi.spyOn(...).mockImplementation
 *   M1-jest    — jest.mock, jest.spyOn, jest.unstable_mockModule
 *   M2-network — msw.setupServer, nock, fetch-mock, axios-mock-adapter
 *
 * Auto-mock directories (`__mocks__/`) are enforced by a separate filesystem
 * check, not this rule.
 */

import type { Rule } from "eslint";

type AstNode = {
  type: string;
  parent?: AstNode | null;
  [key: string]: unknown;
};

const VITEST_MOCK_PROPERTIES: ReadonlySet<string> = new Set([
  "mock",
  "doMock",
  "importMock",
  "hoisted",
  "stubGlobal",
  "stubEnv",
]);

const JEST_MOCK_PROPERTIES: ReadonlySet<string> = new Set([
  "mock",
  "doMock",
  "unstable_mockModule",
  "spyOn",
]);

const NETWORK_MOCK_LIBRARIES: ReadonlySet<string> = new Set([
  "msw",
  "msw/node",
  "msw/browser",
  "nock",
  "fetch-mock",
  "axios-mock-adapter",
]);

const SPY_MODIFIER_METHODS: ReadonlySet<string> = new Set([
  "mockReturnValue",
  "mockReturnValueOnce",
  "mockResolvedValue",
  "mockResolvedValueOnce",
  "mockRejectedValue",
  "mockRejectedValueOnce",
  "mockImplementation",
  "mockImplementationOnce",
]);

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

function isNamespaceCall(node: AstNode, namespace: string, propertySet: ReadonlySet<string>): string | null {
  const callee = node.callee as AstNode | undefined;
  if (!callee || callee.type !== "MemberExpression" || callee.computed === true) return null;
  const object = callee.object as AstNode | undefined;
  const property = callee.property as AstNode | undefined;
  if (!object || !property) return null;
  if (object.type !== "Identifier" || object.name !== namespace) return null;
  if (property.type !== "Identifier" || typeof property.name !== "string") return null;
  if (!propertySet.has(property.name)) return null;
  return `${namespace}.${property.name}`;
}

function isSpyModifierCall(node: AstNode): string | null {
  const callee = node.callee as AstNode | undefined;
  if (!callee || callee.type !== "MemberExpression" || callee.computed === true) return null;

  const property = callee.property as AstNode | undefined;
  if (!property || property.type !== "Identifier" || typeof property.name !== "string") return null;
  if (!SPY_MODIFIER_METHODS.has(property.name)) return null;

  // The object of the modifier must itself be a spy call: vi.spyOn(...) or jest.spyOn(...)
  const object = callee.object as AstNode | undefined;
  if (!object || object.type !== "CallExpression") return null;

  const spyCallee = object.callee as AstNode | undefined;
  if (!spyCallee || spyCallee.type !== "MemberExpression" || spyCallee.computed === true) return null;

  const spyNamespace = spyCallee.object as AstNode | undefined;
  const spyProperty = spyCallee.property as AstNode | undefined;
  if (!spyNamespace || spyNamespace.type !== "Identifier") return null;
  if (!spyProperty || spyProperty.type !== "Identifier") return null;
  if (spyProperty.name !== "spyOn") return null;
  if (spyNamespace.name !== "vi" && spyNamespace.name !== "jest") return null;

  return `${spyNamespace.name}.spyOn(...).${property.name}`;
}

const rule: Rule.RuleModule = {
  meta: {
    type: "suggestion",
    docs: {
      description: "Surface mock-API call sites for Gate 1 exception judgment",
    },
    messages: {
      mockApi:
        "Mock API call site: `{{api}}`. Gate 1 audits this against the /testing exception catalog (1-7). Ensure an exception applies or replace with a class/object implementing the real interface.",
    },
  },

  create(context) {
    function report(node: AstNode, api: string) {
      context.report({
        node: node as unknown as Rule.Node,
        messageId: "mockApi",
        data: { api },
      });
    }

    return {
      CallExpression(node) {
        const n = node as unknown as AstNode;

        const viCall = isNamespaceCall(n, "vi", VITEST_MOCK_PROPERTIES);
        if (viCall !== null) {
          report(n, viCall);
          return;
        }

        const jestCall = isNamespaceCall(n, "jest", JEST_MOCK_PROPERTIES);
        if (jestCall !== null) {
          report(n, jestCall);
          return;
        }

        const spyModifier = isSpyModifierCall(n);
        if (spyModifier !== null) {
          report(n, spyModifier);
          return;
        }

        // Bare `nock(host)` call — nock is imported as a function
        const calleePath = getCalleePath(n.callee as AstNode);
        if (calleePath === "nock") {
          report(n, "nock");
          return;
        }

        // msw.setupServer(...) and similar lifecycle calls
        if (
          calleePath === "setupServer"
          || calleePath === "setupWorker"
          || calleePath === "fetchMock"
        ) {
          report(n, calleePath);
        }
      },
      ImportDeclaration(node) {
        if (typeof node.source.value !== "string") return;
        if (NETWORK_MOCK_LIBRARIES.has(node.source.value)) {
          context.report({
            node,
            messageId: "mockApi",
            data: { api: `import ${node.source.value}` },
          });
        }
      },
    };
  },
};

export default rule;
