# A check-full recipe that runs only the test recipe, so no static-analysis step runs
check-full:
    python3 -m outcomeeng.validation test
