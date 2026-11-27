with flagged as (
  select url, case when lag(viewed_at) over w is null or viewed_at - lag(viewed_at) over w > interval '30 minutes'
                   then 1 else 0 end as new_session
  from pageviews window w as (partition by user_id order by viewed_at, id)
)
select url, count(*) as sessions from flagged where new_session = 1 group by url order by sessions desc, url;
