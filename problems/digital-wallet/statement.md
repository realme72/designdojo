# Digital Wallet (Paytm / PhonePe)

Design a wallet service: balances, deposits, withdrawals, transfers and a per-wallet ledger.
All amounts are integer cents.

## Requirements

1. `create_wallet(user)`; repeated → `DuplicateWallet`. Unknown user anywhere → `UnknownWallet`.
2. `deposit(user, amount)` / `withdraw(user, amount)` return the new balance.
   `amount ≤ 0` → `InvalidAmount`; withdrawing more than the balance → `InsufficientFunds`.
3. `transfer(from_user, to_user, amount, idempotency_key)` moves money atomically and returns
   `{id, from_user, to_user, amount}`. Checks, in order: unknown wallet, `amount ≤ 0` →
   `InvalidAmount`, same wallet → `SameWallet`, `amount > max_transfer` (config) →
   `LimitExceeded`, insufficient balance → `InsufficientFunds`.
4. **Idempotency**: repeating a *successful* transfer with the same key returns the original
   transaction and moves no money. The same key with different parameters →
   `IdempotencyConflict`. A failed attempt does not consume its key.
5. `balance(user)`; `history(user)` lists ledger entries in order:
   `{type, amount, balance_after}` with types `DEPOSIT`, `WITHDRAWAL`, `TRANSFER_IN`,
   `TRANSFER_OUT`.
6. Transfers run concurrently in both directions: never lose or create money, never go
   negative, never deadlock.

## Things an interviewer will push on

- How do you lock two wallets without deadlocking?
- Why is idempotency essential for payment APIs? Where are keys stored, for how long?
- Ledger vs balance column: which is the source of truth?
