import parser from "@typescript-eslint/parser";

export default [
  {
    ignores: [
      "node_modules/**",
      "**/.venv/**",
      "**/dist/**",
    ],
  },
  {
    files: ["**/*.ts"],
    languageOptions: {
      parser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
    // This marketplace validates TypeScript syntax for plugin examples and
    // embedded lint-rule sources. It does not ship a TypeScript lint policy.
    rules: {},
  },
];
