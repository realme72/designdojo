select c.email,
       count(distinct o.id)               as orders,
       sum(i.quantity * i.unit_price)     as total_spent
from customers c
join orders o      on o.customer_id = c.id and o.status <> 'CANCELLED'
join order_items i on i.order_id = o.id
group by c.id, c.email
order by total_spent desc, c.email
limit :n;
