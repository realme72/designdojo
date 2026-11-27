with s as (   -- CHECK (qty >= 0) refuses overselling; no stock row means nothing to ship
  update stock set qty = qty - :qty::int
  where warehouse_id = :warehouse_id and product_id = :product_id and :qty::int > 0
  returning warehouse_id, product_id
)
insert into movements (warehouse_id, product_id, change, reason)
select warehouse_id, product_id, -:qty::int, 'SHIP' from s
union all
select :warehouse_id, :product_id, null, 'SHIP' where not exists (select 1 from s);   -- refuse
