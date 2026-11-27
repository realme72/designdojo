select p.sku, i.quantity as qty, i.unit_price
from order_items i
join products p on p.id = i.product_id
where i.order_id = :order_id
order by p.sku;
