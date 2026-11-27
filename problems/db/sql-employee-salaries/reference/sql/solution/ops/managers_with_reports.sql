select m.name, count(*) as reports
from employees e join employees m on m.id = e.manager_id
group by m.id, m.name having count(*) >= :min
order by reports desc, m.name;
