# Vending Machine

Design a coin-operated vending machine. Coins are `ONE`, `TWO`, `FIVE`, `TEN` (worth 1, 2, 5, 10).

## Requirements

1. The machine starts with a coin float from config (coins it can give as change).
2. `add_product(code, name, price, quantity)` adds a product or, for an existing code,
   updates its name and price and **adds** the quantity. `price < 1` or `quantity < 0`
   → `InvalidProduct`.
3. `insert(coin)` adds a coin to the current session and returns the session balance.
   Inserted coins go into the machine immediately and can be used as change.
4. `select(code)` vends a product. Checks, in order: unknown code → `UnknownProduct`;
   none left → `SoldOut`; balance < price → `InsufficientFunds`; exact change impossible
   → `CannotMakeChange`. A failed `select` changes nothing (the balance is kept).
   On success: stock −1, change dispensed, session ends (balance 0).
5. **Change** must be exact, using the **fewest coins** possible from what the machine holds.
   If several sets have the same count, prefer higher-value coins. Coins are listed from
   highest to lowest value.
6. `cancel()` ends the session and returns exactly the coins inserted in it (highest value
   first). With no session, it returns an empty list.
7. `balance()` is the current session balance; `stock(code)` the remaining quantity.

## Things an interviewer will push on

- Which states does the machine have, and which actions are legal in each?
- Why is greedy change-making not always enough when coins run out?
- How would you add card payments or a maintenance mode?
