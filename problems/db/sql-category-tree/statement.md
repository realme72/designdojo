# Category Tree

> **Interview questions** (tab next to Problem): start there.

Schema given: `categories(id, parent_id, name)` (a tree; roots have NULL parent) and
`products(id, category_id, name, price)`.

| Query | Returns |
|---|---|
| `path(:category_id)` | a single value like `Electronics > Phones > Android` |
| `subtree_products(:category_id)` | one row: `products`, `avg_price` (2 decimals, NULL if none): products in the category and all its descendants |
| `outline()` | rows `name`, `depth`: the whole tree depth-first (roots depth 0), siblings by name |
| `leaf_categories()` | rows `name`: categories without children, by name |
