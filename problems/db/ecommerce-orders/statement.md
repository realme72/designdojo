# E-commerce Orders

> **Interview questions** (tab next to Problem): start there, like a real interview. Should this be
> relational or NoSQL, and why? How do you stop races? What would you index? Answer in your own words and
> get graded on the reasoning, then design the schema.

Design the database behind a small online store, then write the operations and reports it
needs. The judge runs your `schema.sql` on an empty **PostgreSQL 17** database and calls your
operations. Invalid data must be **rejected by the database** (constraints), not merely
avoided by careful callers.

## Requirements

1. **Customers** have a name and an email. Emails are unique **ignoring case**
   (`Ann@x.com` and `ann@x.com` are the same customer).
2. **Products** have a unique SKU, a name, a price (money, never negative) and a stock count
   (never negative).
3. A customer places **orders**. An order has a status: `PLACED` (initially), `PAID`,
   `SHIPPED` or `CANCELLED`. Nothing else is a valid status.
4. An order has one or more **lines**: a product and a quantity (at least 1). A product
   appears at most once per order.
5. **Prices change** over time, but an existing order must keep the price it was placed at.
6. Placing an order **takes the items out of stock**. If any line can't be fulfilled
   (unknown product, not enough stock, bad quantity, unknown customer) the whole order is
   rejected and nothing changes.

## Operations

Each lives in `solution/ops/<name>.sql` and uses `:param` placeholders (see
`contract/operations.sql`). Each runs atomically.

| Operation | Returns |
|---|---|
| `add_customer(:email, :name)` | one row: `id` |
| `add_product(:sku, :name, :price, :stock)` | one row: `id` |
| `set_price(:product_id, :price)` | nothing |
| `place_order(:customer_id, :items)` | one row: `order_id`, `total` |
| `set_status(:order_id, :status)` | nothing |
| `order_lines(:order_id)` | rows `sku`, `qty`, `unit_price`, by `sku` |
| `top_customers(:n)` | rows `email`, `orders`, `total_spent`: the `n` biggest spenders |
| `never_ordered()` | rows `sku` of products that never appeared on any order, by `sku` |

`:items` is JSON: `[{"product_id": 1, "qty": 2}, ...]`
(`jsonb_array_elements(:items)` turns it into rows).

`top_customers` ignores `CANCELLED` orders and customers without (other) orders; highest
`total_spent` first, ties by email. `orders` counts the customer's non-cancelled orders.

## Example

```
add_product('A-1', 'Mug', 19.99, 10) -> {id: 1}
place_order(1, [{"product_id": 1, "qty": 2}]) -> {order_id: 1, total: 39.98}
set_price(1, 24.99)
order_lines(1) -> [{sku: A-1, qty: 2, unit_price: 19.99}]   -- old price kept
```
