with m as (
  select date_trunc('month', ordered_at at time zone 'UTC')::date as month, sum(amount) as revenue
  from orders group by 1
)
select month, revenue,
       round(100 * (revenue - lag(revenue) over w) / nullif(lag(revenue) over w, 0), 1) as growth_pct
from m window w as (order by month)
order by month;
