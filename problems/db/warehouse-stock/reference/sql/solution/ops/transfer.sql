with out as (
  update stock set qty = qty - :qty::int
  where warehouse_id = :from_id and product_id = :product_id
    and :qty::int > 0 and :from_id::bigint <> :to_id::bigint
  returning product_id
),
inn as (
  insert into stock (warehouse_id, product_id, qty)
  select :to_id, product_id, :qty from out
  on conflict (warehouse_id, product_id) do update set qty = stock.qty + excluded.qty
)
insert into movements (warehouse_id, product_id, change, reason)
select x.w, out.product_id, x.c, 'TRANSFER'
from out, (values (:from_id::bigint, -:qty::int), (:to_id::bigint, :qty::int)) as x(w, c)
union all
select :from_id, :product_id, null, 'TRANSFER' where not exists (select 1 from out);   -- refuse
