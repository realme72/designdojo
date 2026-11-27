with recursive tree as (
  select id, body, 0 as depth, array[id] as path
  from comments where post_id = :post_id and parent_id is null
  union all
  select c.id, c.body, t.depth + 1, t.path || c.id
  from comments c join tree t on c.parent_id = t.id and c.post_id = :post_id
)
select id, depth, body from tree order by path;
