with recursive up (id, parent_id, name, depth) as (
  select f.id, f.parent_id, f.name, 1 from folders f join files x on x.folder_id = f.id where x.id = :file_id
  union all
  select f.id, f.parent_id, f.name, up.depth + 1 from folders f join up on f.id = up.parent_id
)
select '/' || string_agg(name, '/' order by depth desc) || '/' || (select name from files where id = :file_id)
from up;
