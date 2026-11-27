with u as (select id, date_trunc('month', signed_up_at at time zone 'UTC')::date as cohort from users),
sizes as (select cohort, count(*) as size from u group by cohort),
act as (
  select u.cohort,
         ((extract(year from a.active_on) - extract(year from u.cohort)) * 12
          + extract(month from a.active_on) - extract(month from u.cohort))::int as month_offset,
         count(distinct a.user_id) as retained
  from activity a join u on u.id = a.user_id
  group by 1, 2
)
select s.cohort, g.month_offset, coalesce(a.retained, 0) as retained,
       round(100.0 * coalesce(a.retained, 0) / s.size, 1) as pct
from sizes s cross join generate_series(0, :max_offset) as g(month_offset)
left join act a on a.cohort = s.cohort and a.month_offset = g.month_offset
order by s.cohort, g.month_offset;
