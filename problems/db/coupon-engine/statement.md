# Coupon Engine

> **Interview questions** (tab next to Problem): start there.

Design coupon storage and redemption for a store (**PostgreSQL 17**). Limits must hold even when
thousands of shoppers redeem at once.

## Requirements

1. A **coupon** has a unique code (case-insensitive: `SAVE10` = `save10`) and **either** a
   percentage off (1–100) **or** a flat amount off (> 0), never both. It has a minimum order
   value, a validity window `[valid_from, valid_to)`, a **global** limit on redemptions and a
   **per-user** limit.
2. A **redemption** records the user, the coupon, the order total and the discount given.
   Discount = percentage of the order (rounded to 2 decimals) or the flat amount, but never more
   than the order total.
3. Redeeming is rejected if the coupon doesn't exist, isn't valid at that time, the order is
   below the minimum, or either limit is already reached.

## Operations

| Operation | Returns |
|---|---|
| `create_coupon(:code, :percent_off, :flat_off, :min_order, :max_uses, :per_user, :valid_from, :valid_to)` | one row: `id` (one of `:percent_off` / `:flat_off` is NULL) |
| `redeem(:code, :user_id, :order_total, :at)` | one row: `discount` |
| `usage_report()` | rows `code`, `uses`, `total_discount`: every coupon, by code |
