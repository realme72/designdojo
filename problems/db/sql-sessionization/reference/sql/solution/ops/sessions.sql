with flagged as (
  select *, case when lag(viewed_at) over w is null or viewed_at - lag(viewed_at) over w > interval '30 minutes'
                 then 1 else 0 end as new_session
  from pageviews window w as (partition by user_id order by viewed_at, id)
),
numbered as (
  select *, sum(new_session) over (partition by user_id order by viewed_at, id) as session_no from flagged
)
select user_id, session_no, min(viewed_at) as started_at, max(viewed_at) as ended_at, count(*) as views
from numbered group by user_id, session_no order by user_id, session_no;
