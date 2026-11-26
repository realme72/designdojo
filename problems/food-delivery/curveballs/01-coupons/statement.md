# Coupons

Marketing wants coupons. `add_coupon(code, percent_off, max_off)` registers one;
`apply_coupon(order_id, code)` applies it to an order that is still `PLACED` and returns the
updated order. Discount = `min(items subtotal × percent_off / 100 (rounded down), max_off)`;
the delivery fee is never discounted. One coupon per order. Unknown code, or a second coupon on
the same order → `InvalidCoupon`; order no longer `PLACED` → `InvalidState`.

*Interviewer's question:* where does price calculation live once there are three kinds of discount?
