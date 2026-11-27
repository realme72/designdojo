select region,
       coalesce(sum(amount) filter (where extract(quarter from sold_on) = 1), 0) as q1,
       coalesce(sum(amount) filter (where extract(quarter from sold_on) = 2), 0) as q2,
       coalesce(sum(amount) filter (where extract(quarter from sold_on) = 3), 0) as q3,
       coalesce(sum(amount) filter (where extract(quarter from sold_on) = 4), 0) as q4,
       sum(amount) as total
from sales where extract(year from sold_on) = :year
group by region order by region;
