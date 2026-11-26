# Bundle pricing

Marketing wants "3 for 250". Add promotion kind `BUNDLE_PRICE` (automatic, item-level):

- For SKU `sku`, every group of `threshold` units costs `value` cents in total. The discount
  is `groups × (threshold × unit_price − value)`, and never negative.
- Validation: `threshold ≥ 1`, `value ≥ 1`, known SKU → else `InvalidPromotion`.
- It competes with other item promotions on the same SKU: still only the biggest discount applies.
- Applying it as a coupon → `InvalidCoupon` (it is item-level).

*Interviewer's question:* did the pricing engine change, or only the set of promotions?
