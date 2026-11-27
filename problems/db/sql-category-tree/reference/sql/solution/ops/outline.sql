with recursive t (id, name, depth, path) as (
  select id, name, 0, array[name] from categories where parent_id is null
  union all
  select c.id, c.name, t.depth + 1, t.path || c.name from categories c join t on c.parent_id = t.id
)
select name, depth from t order by path;
