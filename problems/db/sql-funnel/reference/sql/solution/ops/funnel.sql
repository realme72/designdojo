with firsts as (
  select user_id, min(at) filter (where event_type = 'VIEW') as v from events
  where at >= :from and at < :to group by user_id
),
carts as (
  select f.user_id, f.v, (select min(e.at) from events e where e.user_id = f.user_id and e.event_type = 'CART'
                          and e.at >= f.v and e.at < :to) as c
  from firsts f where f.v is not null
),
buys as (
  select c.*, exists (select 1 from events e where e.user_id = c.user_id and e.event_type = 'PURCHASE'
                      and e.at >= c.c and e.at < :to) as p
  from carts c
)
select count(*) as viewed, count(c) as carted, count(*) filter (where p) as purchased from buys;
