select name, rating, created_at from (
  select distinct on (r.product_id) p.name, r.rating, r.created_at
  from reviews r join products p on p.id = r.product_id
  order by r.product_id, r.created_at desc, r.id desc
) x order by name;
