with recursive up (id, owner_id, parent_id) as (
  select f.id, f.owner_id, f.parent_id from folders f join files x on x.folder_id = f.id where x.id = :file_id
  union all
  select f.id, f.owner_id, f.parent_id from folders f join up on f.id = up.parent_id
)
select exists (
  select 1 from up where owner_id = :user_id
  union all
  select 1 from up join shares s on s.folder_id = up.id and s.user_id = :user_id
);
