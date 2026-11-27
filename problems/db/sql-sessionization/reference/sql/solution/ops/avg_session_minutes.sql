with flagged as (
  select *, case when lag(viewed_at) over w is null or viewed_at - lag(viewed_at) over w > interval '30 minutes'
                 then 1 else 0 end as new_session
  from pageviews window w as (partition by user_id order by viewed_at, id)
),
numbered as (select *, sum(new_session) over (partition by user_id order by viewed_at, id) as s from flagged),
lens as (select extract(epoch from max(viewed_at) - min(viewed_at)) / 60 as minutes from numbered group by user_id, s)
select round(avg(minutes)::numeric, 1) from lens;
