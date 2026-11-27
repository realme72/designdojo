with firsts as (
  select user_id, min(at) filter (where event_type = 'VIEW') as v from events
  where at >= :from and at < :to group by user_id
),
steps as (
  select f.user_id, f.v,
         (select min(e.at) from events e where e.user_id = f.user_id and e.event_type = 'CART' and e.at >= f.v and e.at < :to) as c
  from firsts f where f.v is not null
)
select (v at time zone 'UTC')::date as day, count(*) as viewed,
       count(*) filter (where exists (select 1 from events e where e.user_id = steps.user_id and e.event_type = 'PURCHASE'
                                      and e.at >= steps.c and e.at < :to)) as purchased
from steps group by 1 order by 1;
