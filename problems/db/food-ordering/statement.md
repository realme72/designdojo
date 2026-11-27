# Food Ordering (Swiggy)

> **Interview questions** (tab next to Problem): start there.

Design the order database of a food-delivery app (**PostgreSQL 17**).

## Requirements

1. **Restaurants** have menu **items** (name, price ≥ 0, available or not). **Customers** and
   delivery **agents** have names.
2. An **order** is from one customer at one restaurant. Every line's item must belong to
   **that restaurant** and be available; quantities are ≥ 1. The order keeps the prices paid
   and its total.
3. Order **status** moves only along `PLACED → PREPARING → PICKED_UP → DELIVERED`, or
   `PLACED → CANCELLED`. Any other change is rejected.
4. An **agent** carries at most **one active order** (assigned and not yet delivered or
   cancelled) at a time.

## Operations

| Operation | Returns |
|---|---|
| `add_restaurant(:name)`, `add_customer(:name)`, `add_agent(:name)` | one row: `id` |
| `add_item(:restaurant_id, :name, :price)` | one row: `id` |
| `set_available(:item_id, :available)` | nothing |
| `place_order(:customer_id, :restaurant_id, :items)` | one row: `order_id`, `total` (`:items` JSON `[{"item_id": 1, "qty": 2}]`) |
| `assign_agent(:order_id, :agent_id)` | nothing |
| `advance(:order_id, :status)` | nothing |
| `restaurant_revenue(:restaurant_id)` | a single value: total of its DELIVERED orders (0 if none) |
| `agent_deliveries()` | rows `agent`, `delivered`: every agent, by name |
