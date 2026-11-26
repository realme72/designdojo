# ATM

Design the software of a single ATM: card sessions, PIN checks, balance, withdrawals
from limited note cassettes, and deposits. (All data is fake test data.)

## Requirements

1. Config: the notes loaded (`denomination → count`) and the bank's accounts
   (`card`, `pin`, `balance`).
2. The ATM is in one of three states: no card → card inserted → authenticated.
   Any operation not allowed in the current state → `InvalidState`.
3. `insert_card(card)`: unknown card → `UnknownCard`; blocked card → `CardBlocked`.
4. `enter_pin(pin)`: correct → authenticated. Wrong → `WrongPin`. The **third consecutive
   wrong PIN** for a card (counted across sessions; a correct PIN resets the count) blocks
   the card, ends the session and raises `CardBlocked`.
5. `balance()` and `deposit(amount)` (returns the new balance) need authentication.
   `deposit` with `amount ≤ 0` → `InvalidAmount`.
6. `withdraw(amount)` returns the notes dispensed as `{value, count}`, highest value first.
   Checks, in order: `amount ≤ 0` → `InvalidAmount`; more than the balance →
   `InsufficientFunds`; can't be made exactly from the notes in the ATM → `CannotDispense`.
   Use the **fewest notes** possible (ties: prefer higher notes). A failed withdrawal
   changes nothing.
7. `eject()` ends the session (needs a card). `cash()` is the total value of notes inside.

## Things an interviewer will push on

- Model the states: where do the "is this allowed now?" checks live?
- How do you dispense when the 500s run out? Is greedy enough?
- How would you add a second bank or a "change PIN" flow?
