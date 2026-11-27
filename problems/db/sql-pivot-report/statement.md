# Pivot & Subtotals

> **Interview questions** (tab next to Problem): start there.

Schema given: `sales(id, region, product, sold_on, amount)`.

| Query | Returns |
|---|---|
| `quarterly(:year)` | rows `region`, `q1`, `q2`, `q3`, `q4`, `total`: one row per region with sales that year, each quarter's sum (0 if none); by region |
| `with_subtotals(:year)` | rows `region`, `product`, `total`: per region+product, a subtotal per region (product NULL) and a grand total (both NULL) last; regions alphabetical with their subtotal after their products |
| `best_product_share(:year)` | rows `region`, `product`, `share_pct`: each region's top product and its share of the region's total, 1 decimal; by region |
