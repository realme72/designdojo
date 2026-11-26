# Shopping Cart & Promotions

Design the cart and pricing engine of an online store. All money is integer cents.

## Requirements

1. `add_product(sku, name, price)` adds or re-prices a product (`price < 1` → `InvalidPrice`).
   Bills always use **current** prices.
2. `add_to_cart(cart_id, sku, qty)` adds quantity (carts are created on first use);
   `remove_from_cart(cart_id, sku, qty)` removes up to `qty` (the line disappears at 0).
   Unknown SKU → `UnknownProduct`; `qty < 1` → `InvalidQuantity`; removing a SKU not in
   the cart → `NotInCart`.
3. `add_promotion({code, kind, sku, threshold, value})`; repeated code → `DuplicatePromotion`.
   - `PERCENT_OFF_SKU`: `value`% off that SKU's line (rounded down). Automatic.
   - `BUY_X_GET_Y`: for every `threshold` paid units of the SKU, `value` more are free:
     free units = `floor(qty / (threshold + value)) × value`. Automatic.
   - `FLAT_OFF_CART`: `value` cents off. Needs the coupon applied.
   - `PERCENT_OFF_CART`: `value`% off (rounded down). Needs the coupon applied.
   Cart-level promos only apply when the amount after item discounts is ≥ `threshold`.
   Invalid → `InvalidPromotion`: percent outside 1–100, `threshold`/`value` < 1 for
   buy-X-get-Y, `value < 1` for flat, item promos on an unknown SKU.
4. When several item promotions match a SKU, only the one with the **biggest discount**
   applies (no stacking).
5. `apply_coupon(cart_id, code)` sets the cart's single coupon (replacing any previous one).
   Unknown code → `UnknownPromotion`; an item-level promotion code → `InvalidCoupon`.
   A coupon whose threshold isn't met is simply not applied.
6. `bill(cart_id)` returns `{subtotal, discount, total, lines}` with lines sorted by SKU
   (`{sku, qty, unit_price, line_total}` before discounts). `total = subtotal − discount`,
   never below 0. `checkout(cart_id)` returns the bill and empties the cart (coupon too).

## Things an interviewer will push on

- How do you add "spend 1000, get a free bag" without touching existing promotions?
- What's the order of applying item vs cart promotions, and who owns it?
- How would you let promotions stack, or limit them per customer?
