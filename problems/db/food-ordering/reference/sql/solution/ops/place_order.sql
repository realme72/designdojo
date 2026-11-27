with lines as (
  select (x ->> 'item_id')::bigint as item_id, (x ->> 'qty')::int as qty from jsonb_array_elements(:items) x
),
priced as (
  select l.item_id, l.qty,
         (select price from menu_items m where m.id = l.item_id and m.restaurant_id = :restaurant_id and m.available) as price
  from lines l
),
o as (
  insert into orders (customer_id, restaurant_id, total)
  select :customer_id, :restaurant_id, sum(qty * price) from priced
  returning id, restaurant_id, total
),
li as (
  insert into order_items (order_id, restaurant_id, item_id, qty, unit_price)
  select o.id, o.restaurant_id, p.item_id, p.qty, p.price from o, priced p   -- NULL price (unavailable/foreign item) is refused
)
select id as order_id, total from o;
