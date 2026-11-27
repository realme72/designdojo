with per as (
  select date_trunc('month', o.ordered_at at time zone 'UTC')::date as month, c.name as customer, sum(o.amount) as revenue
  from orders o join customers c on c.id = o.customer_id group by 1, 2
)
select distinct on (month) month, customer, revenue from per order by month, revenue desc, customer;
