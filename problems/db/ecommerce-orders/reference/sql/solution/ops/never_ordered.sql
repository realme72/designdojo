select p.sku
from products p
where not exists (select 1 from order_items i where i.product_id = p.id)
order by p.sku;
