with days as (
  select distinct user_id, (logged_at at time zone 'UTC')::date as d from logins
),
islands as (
  select user_id, d - (row_number() over (partition by user_id order by d))::int as grp from days
),
runs as (select user_id, count(*) as len from islands group by user_id, grp)
select u.name, coalesce(max(r.len), 0) as streak
from users u left join runs r on r.user_id = u.id
group by u.id, u.name order by streak desc, u.name;
