for (const row of cases) {
  consume(row);
}

for await (const [input, expected] of asyncCases) {
  assertCase(input, expected);
}

for (let index = 0; index < cases.length; index += 1) {
  consume(cases[index]);
}
