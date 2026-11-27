select u.name, count(i.id) as open
from members m join users u on u.id = m.user_id
left join issues i on i.project_id = m.project_id and i.assignee_id = m.user_id and i.status <> 'DONE'
where m.project_id = :project_id
group by u.id, u.name order by open desc, u.name;
