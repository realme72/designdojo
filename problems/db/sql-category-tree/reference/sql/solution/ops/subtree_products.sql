with recursive down (id) as (
  select :category_id
  union all
  select c.id from categories c join down on c.parent_id = down.id
)
select count(p.id) as products, round(avg(p.price), 2) as avg_price from products p join down on p.category_id = down.id;
