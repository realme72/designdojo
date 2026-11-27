# Conversion Funnel

> **Interview questions** (tab next to Problem): start there.

Schema given: `events(user_id, event_type, at)` with types `VIEW`, `CART`, `PURCHASE`.

A user **reached** a step only by doing the steps **in order**: viewed, then carted at or
after their first view, then purchased at or after that first cart. Only events inside
`[from, to)` count.

| Query | Returns |
|---|---|
| `funnel(:from, :to)` | one row: `viewed`, `carted`, `purchased`: users reaching each step |
| `conversion(:from, :to)` | one row: `view_to_cart_pct`, `cart_to_purchase_pct`, `overall_pct`: percentages with 1 decimal (NULL when dividing by 0) |
| `daily_funnel(:from, :to)` | rows `day`, `viewed`, `purchased`: per UTC day of the **first view**, users who viewed and users who (in order) purchased; days with views only, by day |
