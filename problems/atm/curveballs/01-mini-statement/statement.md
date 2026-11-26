# Mini statement

Customers want to see recent activity. Add `mini_statement()` (authenticated only, else
`InvalidState`): the card's last **5** successful withdrawals and deposits, newest first, as
`{type, amount, balance_after}` with types `WITHDRAWAL` / `DEPOSIT`. Failed operations are not
listed. History belongs to the card (it survives sessions).

*Interviewer's question:* who owns transaction history: the ATM session, the account, or a ledger?
