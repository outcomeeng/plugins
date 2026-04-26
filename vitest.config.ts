import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["spx/**/*.test.ts"],
    exclude: ["**/*.e2e.test.ts", "**/*.playwright.test.ts", "**/node_modules/**"],
    passWithNoTests: false,
  },
});
