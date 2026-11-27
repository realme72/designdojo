with firsts as (
  select user_id, min(at) filter (where event_type = 'VIEW') as v from events
  where at >= :from and at < :to group by user_id
),
carts as (
  select f.user_id, (select min(e.at) from events e where e.user_id = f.user_id and e.event_type = 'CART'
                     and e.at >= f.v and e.at < :to) as c
  from firsts f where f.v is not null
),
f as (
  select count(*) as viewed, count(c) as carted,
         count(*) filter (where exists (select 1 from events e where e.user_id = carts.user_id and e.event_type = 'PURCHASE'
                                        and e.at >= carts.c and e.at < :to)) as purchased
  from carts
)
select round(100.0 * carted / nullif(viewed, 0), 1) as view_to_cart_pct,
       round(100.0 * purchased / nullif(carted, 0), 1) as cart_to_purchase_pct,
       round(100.0 * purchased / nullif(viewed, 0), 1) as overall_pct
from f;
