/**
 * Default policy for `no-literal-test-numbers`.
 *
 * `allowedRawNumbers` are structural constants safe to use inline (array
 * indices, small counters, sentinel values). `alwaysNamedCallsites` force
 * numbers to be named regardless of value — precision and tolerance arguments
 * must carry a meaningful identifier.
 */

export type AlwaysNamedCallsite = {
  readonly calleePropertyNames: readonly string[];
  readonly argumentIndex: number;
};

export type TestNumberPolicy = {
  readonly allowedRawNumbers: readonly number[];
  readonly alwaysNamedCallsites: readonly AlwaysNamedCallsite[];
};

export const TEST_NUMBER_POLICY: TestNumberPolicy = {
  allowedRawNumbers: [-1, 0, 1, 2],
  alwaysNamedCallsites: [
    // Precision matchers — the precision digit count is meaningful and must be named
    {
      calleePropertyNames: ["toBeCloseTo"],
      argumentIndex: 1,
    },
  ],
};
