select e.name, m.name as manager from employees e join employees m on m.id = e.manager_id
where e.salary > m.salary order by e.name;
