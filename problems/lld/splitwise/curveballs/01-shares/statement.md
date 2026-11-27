# Split by shares

Groups want "Ann pays 2 shares, everyone else 1". Add split type `SHARES`:

- Each `value` is a number of shares (≥ 0); the total must be ≥ 1 → else `InvalidSplit`.
- Each share is `floor(amount × shares / total_shares)`; leftover cents go one each to the
  first shares **in list order** (the same rule as the other types).

*Interviewer's question:* what did adding a split type cost you?
