with new_order as (
  insert into orders (customer_id) values (:customer_id) returning id
),
items as (
  select (x ->> 'product_id')::bigint as product_id, (x ->> 'qty')::int as qty
  from jsonb_array_elements(:items) as x
),
lines as (
  insert into order_items (order_id, product_id, quantity, unit_price)
  select o.id, i.product_id, i.qty, p.price
  from new_order o
  cross join items i
  left join products p on p.id = i.product_id      -- unknown product -> NULL price -> rejected
  returning product_id, quantity, unit_price
),
taken as (
  update products p
  set stock = p.stock - l.quantity                  -- CHECK (stock >= 0) rejects overselling
  from lines l
  where p.id = l.product_id
  returning p.id
)
select (select id from new_order) as order_id,
       (select sum(quantity * unit_price) from lines) as total;
