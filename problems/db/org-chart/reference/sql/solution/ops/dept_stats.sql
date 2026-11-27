select d.name as department, count(e.id) as headcount, round(avg(e.salary), 2) as avg_salary, max(e.salary) as max_salary
from departments d left join employees e on e.department_id = d.id
group by d.id, d.name order by d.name;
