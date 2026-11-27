with m as (
  insert into movements (warehouse_id, product_id, change, reason)
  values (:warehouse_id, :product_id, :qty, 'RECEIVE') returning warehouse_id, product_id, change
)
insert into stock (warehouse_id, product_id, qty)
select warehouse_id, product_id, change from m where change > 0
union all
select warehouse_id, product_id, null from m where change <= 0
on conflict (warehouse_id, product_id) do update set qty = stock.qty + excluded.qty;
