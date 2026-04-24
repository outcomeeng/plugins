/**
 * Shared signal heuristics for literal-based enforcement.
 *
 * Shared between the per-file ESLint rules and the cross-file detector
 * (ported to `spx validate literals`). Both surfaces agree on what counts
 * as meaningful literal signal.
 */

import { builtinModules } from "node:module";

/** Integer literals with fewer meaningful digits are ignored; floats always kept. */
export const MIN_NUMBER_DIGITS = 4;

/** String literals shorter than this are ignored as low-signal noise. */
export const MIN_STRING_LENGTH = 4;

function nodeBuiltinSpecifiers(): readonly string[] {
  return builtinModules.flatMap((name) => [name, `node:${name}`]);
}

/**
 * Short or common literals that carry no domain meaning. The default set covers
 * values that appear in virtually every TypeScript codebase — adding anything
 * project-specific (brand names, domain discriminators, proprietary tokens)
 * belongs in a consumer override config, not here.
 */
export const COMMON_LITERAL_ALLOWLIST: ReadonlySet<string> = new Set([
  // JS sentinel values
  "true",
  "false",
  "null",
  "undefined",

  // JS type names (typeof results)
  "string",
  "number",
  "object",
  "function",
  "symbol",
  "bigint",
  "boolean",

  // JS keywords frequently appearing as strings
  "const",
  "let",
  "var",

  // HTTP methods
  "GET",
  "POST",
  "PUT",
  "DELETE",
  "PATCH",
  "HEAD",
  "OPTIONS",

  // Common MIME types
  "application/json",
  "text/plain",
  "text/html",

  // Encoding names
  "utf-8",
  "utf8",

  // Common CSS keywords
  "none",
  "auto",
  "inherit",
  "block",
  "flex",
  "grid",
  "default",
  "dark",
  "light",

  // Node.js builtin module specifiers (both `fs` and `node:fs` forms)
  ...nodeBuiltinSpecifiers(),
]);

export function isMeaningfulString(value: string): boolean {
  if (value.length < MIN_STRING_LENGTH) return false;
  if (COMMON_LITERAL_ALLOWLIST.has(value)) return false;
  return true;
}

export function isMeaningfulNumber(value: number): boolean {
  const asStr = String(value);
  if (asStr.includes(".")) return true;
  const digits = asStr.replace(/[^0-9]/g, "").length;
  return digits >= MIN_NUMBER_DIGITS;
}
