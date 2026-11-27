with t as (
  select region, product, sum(amount) as total, sum(sum(amount)) over (partition by region) as region_total
  from sales where extract(year from sold_on) = :year group by region, product
)
select distinct on (region) region, product, round(100 * total / region_total, 1) as share_pct
from t order by region, total desc, product;
