select p.sku, coalesce(sum(s.qty), 0) as total
from products p left join stock s on s.product_id = p.id
group by p.id, p.sku
having coalesce(sum(s.qty), 0) < :threshold
order by p.sku;
