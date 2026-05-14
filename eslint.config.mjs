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
    rules: {},
  },
];
