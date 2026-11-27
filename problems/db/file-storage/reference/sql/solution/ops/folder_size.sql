with recursive down (id) as (
  select :folder_id::bigint
  union all
  select f.id from folders f join down on f.parent_id = down.id
)
select coalesce(sum(x.size_bytes), 0) from files x join down on x.folder_id = down.id;
