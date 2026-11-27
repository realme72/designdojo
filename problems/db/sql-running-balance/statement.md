# Running Balance & Statements

> **Interview questions** (tab next to Problem): start there.

Schema given: `accounts(id, owner)` and `transactions(id, account_id, posted_at, amount)`
(signed amounts). Balances start at 0. Order transactions by `posted_at`, then `id`.

| Query | Returns |
|---|---|
| `statement(:account_id)` | rows `posted_at`, `amount`, `balance`: every transaction with the running balance |
| `balance_as_of(:account_id, :at)` | a single value: balance including transactions posted at or before `:at` |
| `daily_closing(:account_id, :from_day, :to_day)` | rows `day`, `balance`: end-of-UTC-day balance for every day in the range, carried forward on days without transactions |
| `first_overdraft()` | rows `owner`, `posted_at`: for each account that ever went below 0, the first transaction that took it there; by owner |
