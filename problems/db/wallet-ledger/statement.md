# Wallet Ledger (Double-Entry)

> **Interview questions** (tab next to Problem): start there.

Design the ledger behind a digital wallet (**PostgreSQL 17**). Money is never created or lost.

## Requirements

1. **Accounts** have an owner name. There is also money coming from outside (deposits).
2. Every movement is a **transaction** made of **entries** (account, signed amount). The
   entries of a transaction **sum to zero**: a deposit moves money from an external source
   account into the wallet; a transfer debits one wallet and credits another.
3. A wallet's **balance** can never go below zero.
4. Amounts are positive money values (2 decimals). Clients retry, so every deposit/transfer has
   an **idempotency key**: a retry with the same key returns the same transaction and moves no
   money again.
5. Entries are **append-only**: history is never updated or deleted.

## Operations

| Operation | Returns |
|---|---|
| `open_account(:owner)` | one row: `id` |
| `deposit(:account_id, :amount, :key)` | one row: `txn_id` |
| `transfer(:from_id, :to_id, :amount, :key)` | one row: `txn_id` (rejected if funds are insufficient, same account, or amount ≤ 0) |
| `balance(:account_id)` | a single value |
| `statement(:account_id)` | rows `txn_id`, `amount`, `balance_after`: the account's entries in transaction order with the running balance |
| `unbalanced_transactions()` | rows `txn_id`: transactions whose entries don't sum to zero (should always be empty) |
