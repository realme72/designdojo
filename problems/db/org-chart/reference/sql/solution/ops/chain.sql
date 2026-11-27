with recursive up (id, name, manager_id, level) as (
  select id, name, manager_id, 0 from employees where id = :employee_id
  union all
  select e.id, e.name, e.manager_id, up.level + 1 from employees e join up on e.id = up.manager_id
)
select name, level from up order by level;
