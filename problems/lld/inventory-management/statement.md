# Inventory Management (Multi-warehouse)

Design stock tracking for an e-commerce company with several warehouses. Orders first
**reserve** stock, then either **commit** (ship) or **release** it.

## Requirements

1. `receive(sku, warehouse, qty)` adds on-hand stock (`qty < 1` → `InvalidQuantity`).
   SKUs and warehouses are created on first receipt.
2. `available(sku)` = on-hand − reserved, summed across warehouses;
   `available_at(sku, warehouse)` for one warehouse. Unknown SKU → `UnknownSku`
   (unknown warehouse for a known SKU → 0).
3. `reserve(order_id, lines)` reserves every line `{sku, qty}` **all-or-nothing**. Each line
   is taken from warehouses in **name order**, as much as possible from each before moving
   on. Not enough stock for any line → `OutOfStock` and nothing is reserved. Repeated
   order id → `DuplicateOrder`; empty lines or `qty < 1` → `InvalidQuantity`;
   unknown SKU → `UnknownSku`. Returns the allocations `{sku, warehouse, qty}` in order.
4. `commit(order_id)` ships the reservation (on-hand decreases); `release(order_id)`
   returns it to available. Both end the reservation; afterwards (or for an unknown
   order) → `UnknownOrder`.
5. `set_threshold(sku, threshold)`; `low_stock()` lists SKUs whose total available is
   **below** their threshold, sorted.
6. Many checkouts reserve at once: never reserve more than is available.

## Things an interviewer will push on

- How would you add a smarter allocation strategy (nearest warehouse, fewest splits)?
- How do low-stock alerts reach purchasing (events/observers)?
- What happens to reservations that are never committed (timeouts)?
