select name, department from (
  select e.name, d.name as department, e.salary, avg(e.salary) over (partition by e.department_id) as dept_avg
  from employees e join departments d on d.id = e.department_id
) x where salary > dept_avg order by name;
