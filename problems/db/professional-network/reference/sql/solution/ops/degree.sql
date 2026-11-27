with recursive bfs (user_id, depth) as (
  select :from_id::bigint, 0
  union
  select l.other_id, b.depth + 1
  from bfs b join user_links l on l.user_id = b.user_id
  where b.depth < 3
)
select min(depth) from bfs where user_id = :to_id and depth > 0;
