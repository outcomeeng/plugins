try {
  throw new Error("case");
} catch (error) {
  expect(error).toBeDefined();
}
