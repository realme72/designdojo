# Splitwise

Design the core of an expense-sharing app: users add shared expenses, the app tracks who
owes whom, and suggests how to settle up. All amounts are integer **cents**.

## Requirements

1. `add_user(user_id)`; a second add of the same id → `DuplicateUser`.
2. `add_expense(paid_by, amount, split_type, shares)` records an expense paid in full by
   `paid_by` and split between the users in `shares` (the payer may or may not be one of them).
   Returns a unique expense id.
   - `EQUAL`: `value` is ignored. Each share is `amount / n` cents; the leftover cents go
     one each to the first shares **in list order**.
   - `EXACT`: each `value` is that user's share in cents; values must sum to `amount`.
   - `PERCENT`: each `value` is a whole percent; percents must sum to 100. Each share is
     `floor(amount * pct / 100)`; leftover cents go one each to the first shares in list order.
3. Invalid expense → `InvalidSplit`: amount ≤ 0, empty shares, a user listed twice, a
   negative value, or sums that don't match. Unknown payer or share user → `UnknownUser`
   (checked first).
4. `balance(user)` is the user's net position: positive means others owe them.
5. `settle(from_user, to_user, amount)` records a payment from one user to another.
   `amount ≤ 0` or paying yourself → `InvalidAmount`.
6. `balances()` lists every user (zeros included) sorted by user id.
7. `simplify()` proposes transfers that clear all debts, without changing any balance:
   repeatedly pair the largest creditor with the largest debtor (ties: smaller user id)
   and transfer the smaller of the two amounts. Return transfers in that order.
8. Many people add expenses at the same time: all operations must be thread-safe.

## Things an interviewer will push on

- How would you add a new split type (e.g. by shares: 2:1:1)?
- Where does the rounding rule live, and is it the same for every split type?
- How would you support groups or multiple currencies?
