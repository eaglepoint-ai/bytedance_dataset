# Problem: TEMP normalize

## Steps:
1) Normalize input with strip + uppercase.
2) If it starts with TEMP, preserve underscores and map each other non-alnum char to '-'.
3) Otherwise, keep the original behavior: collapse runs of non-alnum into a single '-'.
4) Add tests that lock examples and edge cases.
