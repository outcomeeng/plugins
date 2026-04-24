/**
 * Default policy for `no-literal-test-strings`.
 *
 * Descriptive callsites permit string literals — test descriptions, assertion
 * messages, and similar contexts where the literal exists to name the case.
 * Protocol exceptions permit literals whose values are defined by an external
 * standard (ARIA roles, Playwright lifecycle states, DOM attribute names).
 *
 * Consumers can override by shipping an `eslint.audit.config.ts` that provides
 * a different `TestStringPolicy` to the rule.
 */

export type DescriptiveCallsite = {
  readonly callee: string;
  readonly argumentIndex: number;
};

export type ProtocolStringException = {
  readonly calleePropertyNames: readonly string[];
  readonly argumentIndex: number;
  readonly values: readonly string[];
};

export type TestStringPolicy = {
  readonly descriptiveCallsites: readonly DescriptiveCallsite[];
  readonly protocolStringExceptions: readonly ProtocolStringException[];
};

const WAI_ARIA_ROLES: readonly string[] = [
  "alert",
  "article",
  "banner",
  "blockquote",
  "button",
  "caption",
  "cell",
  "checkbox",
  "code",
  "columnheader",
  "combobox",
  "complementary",
  "contentinfo",
  "definition",
  "deletion",
  "dialog",
  "directory",
  "document",
  "emphasis",
  "feed",
  "figure",
  "form",
  "generic",
  "grid",
  "gridcell",
  "group",
  "heading",
  "img",
  "insertion",
  "link",
  "list",
  "listbox",
  "listitem",
  "log",
  "main",
  "marquee",
  "math",
  "menu",
  "menubar",
  "menuitem",
  "menuitemcheckbox",
  "menuitemradio",
  "meter",
  "navigation",
  "none",
  "note",
  "option",
  "paragraph",
  "presentation",
  "progressbar",
  "radio",
  "radiogroup",
  "region",
  "row",
  "rowgroup",
  "rowheader",
  "scrollbar",
  "search",
  "searchbox",
  "separator",
  "slider",
  "spinbutton",
  "status",
  "strong",
  "subscript",
  "superscript",
  "switch",
  "tab",
  "table",
  "tablist",
  "tabpanel",
  "term",
  "textbox",
  "time",
  "timer",
  "toolbar",
  "tooltip",
  "tree",
  "treegrid",
  "treeitem",
];

const PLAYWRIGHT_LOAD_STATES: readonly string[] = [
  "commit",
  "domcontentloaded",
  "load",
  "networkidle",
];

const COMMON_DOM_ATTRIBUTES: readonly string[] = [
  "href",
  "src",
  "alt",
  "class",
  "id",
  "type",
  "role",
  "aria-label",
];

export const TEST_STRING_POLICY: TestStringPolicy = {
  descriptiveCallsites: [
    // Vitest / Jest
    { callee: "test", argumentIndex: 0 },
    { callee: "it", argumentIndex: 0 },
    { callee: "describe", argumentIndex: 0 },
    { callee: "test.each", argumentIndex: 0 },
    { callee: "it.each", argumentIndex: 0 },
    { callee: "describe.each", argumentIndex: 0 },
    { callee: "test.skip", argumentIndex: 0 },
    { callee: "it.skip", argumentIndex: 0 },
    { callee: "test.todo", argumentIndex: 0 },
    { callee: "it.todo", argumentIndex: 0 },
    { callee: "test.only", argumentIndex: 0 },
    { callee: "it.only", argumentIndex: 0 },

    // Playwright test runner
    { callee: "test.describe", argumentIndex: 0 },
    { callee: "test.step", argumentIndex: 0 },

    // Assertion messages — second arg to `expect(value, "because X")`
    { callee: "expect", argumentIndex: 1 },
  ],
  protocolStringExceptions: [
    // Testing-library queries by role
    {
      calleePropertyNames: [
        "getByRole",
        "getAllByRole",
        "findByRole",
        "findAllByRole",
        "queryByRole",
        "queryAllByRole",
      ],
      argumentIndex: 0,
      values: WAI_ARIA_ROLES,
    },

    // Playwright load states
    {
      calleePropertyNames: ["waitForLoadState"],
      argumentIndex: 0,
      values: PLAYWRIGHT_LOAD_STATES,
    },

    // Event listener on("console")
    {
      calleePropertyNames: ["on"],
      argumentIndex: 0,
      values: ["console"],
    },

    // DOM attribute access
    {
      calleePropertyNames: ["getAttribute", "hasAttribute"],
      argumentIndex: 0,
      values: COMMON_DOM_ATTRIBUTES,
    },
  ],
};
