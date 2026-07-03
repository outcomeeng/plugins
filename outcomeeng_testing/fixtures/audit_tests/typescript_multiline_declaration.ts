const {
  source,
  expected: target,
  ...rest
} = caseData;

let [
  input,
  output,
] = pair;

const configured = buildConfig();
