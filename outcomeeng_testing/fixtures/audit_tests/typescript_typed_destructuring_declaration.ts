type Case = {
  input: string;
  expected: string;
  nested: { root: string };
  rest: string;
};

type Pair = [string, string];

const {
  input,
  expected: output,
  nested: { root },
  ...rest
}: Case = loadCase();

let [first, second]: Pair = loadPair();

for (const { input: loopInput, expected: loopExpected }: Case of cases) {
  assertCase(loopInput, loopExpected);
}

test("uses fixtures", async ({ request, page }: TestFixtures) => {
  await request.get(page.url());
});

fc.property(caseArb, ([propertyInput, propertyExpected]: Pair) => {
  assertCase(propertyInput, propertyExpected);
});

const checksSource = (source: string) => source.length > 0;

type Predicate = (typeOnly: string) => boolean;

type MultilinePredicate = (multilineTypeOnly: string) => boolean;

type UnterminatedPredicate = (unterminatedTypeOnly: string) => boolean;

const afterUnterminatedType = (afterUnterminatedRuntime: string) => afterUnterminatedRuntime.length > 0;

interface HandlerBag {
  handler: (interfaceTypeOnly: string) => boolean;
}

const runtimePredicate: (typeAnnotationOnly: string) => boolean = (runtimeValue: string) => runtimeValue.length > 0;
