with n as (   -- the project row lock serializes numbering within a project
  update projects set next_number = next_number + 1 where id = :project_id
  returning id, key, next_number - 1 as number
),
i as (
  insert into issues (project_id, number, title, reporter_id)
  select id, number, :title, :reporter_id from n returning project_id, number
)
select n.key || '-' || i.number as issue_key from i join n on n.id = i.project_id;
