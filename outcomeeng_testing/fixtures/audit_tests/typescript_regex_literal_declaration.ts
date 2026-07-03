const urlPattern = /https?:\/\/example\.com/;
const afterPattern = buildCase();
const arrowPattern = () => /https?:\/\/arrow\.example/.test(source);
const afterArrowPattern = buildCase();

function matchesReturnPattern(source: string) {
  return /https?:\/\/return\.example/.test(source);
}

const divisionValue = total / count;
const afterDivision = buildCase();

switch (source) {
  case /https?:\/\/case\.example/.source:
    break;
}

const afterKeywordPattern = buildCase();
