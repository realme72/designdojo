# Sales Analytics

> **Interview questions** (tab next to Problem): start there.

Schema given: `customers(id, name)`, `orders(id, customer_id, ordered_at, amount)`. Months are
UTC calendar months, written as the first day of the month (e.g. `2030-01-01`).

| Query | Returns |
|---|---|
| `monthly_revenue()` | rows `month`, `revenue`, `growth_pct`: months with orders; growth vs the **previous month with orders**, percentage with 1 decimal (NULL for the first) |
| `running_total(:year)` | rows `month`, `revenue`, `running`: every month of the year (12 rows), zero months included, with the year-to-date running total |
| `top_customer_per_month()` | rows `month`, `customer`, `revenue`: each month's top customer by revenue (ties: name); by month |
