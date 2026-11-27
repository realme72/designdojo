with months as (
  select generate_series(make_date(:year, 1, 1), make_date(:year, 12, 1), interval '1 month')::date as month
),
m as (
  select date_trunc('month', ordered_at at time zone 'UTC')::date as month, sum(amount) as revenue
  from orders group by 1
)
select months.month, coalesce(m.revenue, 0) as revenue,
       sum(coalesce(m.revenue, 0)) over (order by months.month rows between unbounded preceding and current row) as running
from months left join m on m.month = months.month
order by months.month;
