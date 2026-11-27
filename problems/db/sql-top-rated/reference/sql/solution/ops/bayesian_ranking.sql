with g as (select avg(rating) as mean from reviews)
select p.name, round((coalesce(sum(r.rating), 0) + :m * g.mean) / (count(r.id) + :m), 3) as score
from products p left join reviews r on r.product_id = p.id cross join g
group by p.id, p.name, g.mean order by score desc, p.name;
