select region, product, sum(amount) as total
from sales where extract(year from sold_on) = :year
group by rollup (region, product)
order by region nulls last, product nulls last;
