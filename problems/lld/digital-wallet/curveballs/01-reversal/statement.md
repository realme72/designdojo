# Transfer reversal

Support disputes: `reverse(transaction_id)` sends a completed transfer's money back. It
returns the reversal as a new `Transaction` (from the original recipient to the original
sender). Ledgers record `REVERSAL_OUT` for the recipient and `REVERSAL_IN` for the sender.
Unknown id → `UnknownTransaction`; already reversed → `AlreadyReversed`; recipient's balance too
low → `InsufficientFunds` (nothing changes). The transfer limit does not apply to reversals.

*Interviewer's question:* is a reversal a new transaction, or an edit to the old one?
