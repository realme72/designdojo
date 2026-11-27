# Top Rated with Ties

> **Interview questions** (tab next to Problem): start there.

Schema given: `products(id, name, category)` and `reviews(id, product_id, user_id, rating, created_at)`.

| Query | Returns |
|---|---|
| `best_per_category(:min_reviews)` | rows `category`, `name`, `avg_rating`: per category, **all** products tied for the highest average rating among products with at least `:min_reviews` reviews; avg 2 decimals; by category, name |
| `latest_review_per_product()` | rows `name`, `rating`, `created_at`: each reviewed product's most recent review (ties: highest id); by name |
| `bayesian_ranking(:m)` | rows `name`, `score`: products ranked by (sum of ratings + m × global average) ÷ (reviews + m), 3 decimals, unreviewed products included; by score desc, name |
