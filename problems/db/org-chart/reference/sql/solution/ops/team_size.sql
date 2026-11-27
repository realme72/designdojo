with recursive down (id) as (
  select id from employees where manager_id = :employee_id
  union all
  select e.id from employees e join down on e.manager_id = down.id
)
select count(*) from down;
