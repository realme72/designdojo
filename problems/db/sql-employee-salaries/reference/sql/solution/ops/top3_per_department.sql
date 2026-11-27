select department, name, salary from (
  select d.name as department, e.name, e.salary,
         dense_rank() over (partition by e.department_id order by e.salary desc) as r
  from employees e join departments d on d.id = e.department_id
) x where r <= 3
order by department, salary desc, name;
