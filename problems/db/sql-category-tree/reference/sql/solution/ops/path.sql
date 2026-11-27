with recursive up (id, parent_id, name, depth) as (
  select id, parent_id, name, 0 from categories where id = :category_id
  union all
  select c.id, c.parent_id, c.name, up.depth + 1 from categories c join up on c.id = up.parent_id
)
select string_agg(name, ' > ' order by depth desc) from up;
