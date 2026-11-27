with c as (   -- eligible coupon, and take one global use atomically (CHECK uses <= max_uses)
  update coupons set uses = uses + 1
  where lower(code) = lower(:code)
    and :at::timestamptz >= valid_from and :at::timestamptz < valid_to
    and :order_total::numeric >= min_order
  returning id, percent_off, flat_off
),
u as (        -- take one per-user use atomically (trigger enforces per_user)
  insert into coupon_user_uses (coupon_id, user_id, uses)
  select id, :user_id, 1 from c
  on conflict (coupon_id, user_id) do update set uses = coupon_user_uses.uses + 1
  returning coupon_id
),
r as (
  insert into redemptions (coupon_id, user_id, order_total, discount, redeemed_at)
  select c.id, :user_id, :order_total,
         least(:order_total::numeric, coalesce(round(:order_total::numeric * c.percent_off / 100.0, 2), c.flat_off)), :at
  from c
  union all
  select null, :user_id, :order_total, 0, :at where not exists (select 1 from c)   -- not eligible: refuse
  returning discount
)
select discount from r;
