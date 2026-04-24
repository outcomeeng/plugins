import { resolve } from "node:path";

import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@eslint-rules": resolve(
        __dirname,
        "plugins/typescript/skills/standardizing-typescript-tests/eslint-rules",
      ),
    },
  },
  test: {
    include: ["spx/**/*.test.ts"],
    exclude: ["**/*.e2e.test.ts", "**/*.playwright.test.ts", "**/node_modules/**"],
    passWithNoTests: false,
  },
});
