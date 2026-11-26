# Stock Exchange Order Matching

Design the matching engine of an exchange: each symbol has an order book, and incoming
orders trade against resting ones by **price-time priority**.

## Requirements

1. `place_order(trader, symbol, side, type, qty, price)` returns
   `{order_id, status, filled_qty, trades}` for the incoming order.
   `qty < 1`, or a `LIMIT` order with `price < 1` → `InvalidOrder` (`price` is ignored for
   `MARKET`).
2. Matching: a `BUY` matches the lowest-priced `SELL`s (a `LIMIT` buy only while ask ≤ its
   price); a `SELL` matches the highest-priced `BUY`s (a limit sell only while bid ≥ its
   price). At the same price, older orders fill first. **Trades execute at the resting
   order's price.** Each trade is `{buy_order, sell_order, price, qty}`, listed in execution order.
3. A `LIMIT` order's unfilled remainder rests on the book (`OPEN` if nothing filled,
   `PARTIALLY_FILLED` otherwise, `FILLED` when done). A `MARKET` order never rests: any
   remainder is cancelled, so it ends `FILLED` or `CANCELLED`.
4. `cancel(order_id)` cancels a resting order (`OPEN` or `PARTIALLY_FILLED`) and removes
   its remainder from the book. Anything else → `InvalidState`; unknown → `UnknownOrder`.
5. `order(order_id)` → current `{order_id, status, filled_qty, trades}` (trades this order
   took part in, in order). `book(symbol)` → `{bids, asks}` aggregated by price as
   `{price, qty}`: bids high→low, asks low→high.
6. Orders arrive concurrently: no share is ever traded twice or lost.

## Things an interviewer will push on

- Which structures give O(log n) best-price access and FIFO within a price?
- How would you add stop orders, IOC/FOK, or fees?
- One lock per symbol vs a single-threaded sequencer per symbol?
