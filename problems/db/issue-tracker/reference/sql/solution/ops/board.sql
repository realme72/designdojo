select k.status, k.issue_key, u.name as assignee
from issue_keys k left join users u on u.id = k.assignee_id
where k.project_id = :project_id
order by array_position(array['TODO', 'IN_PROGRESS', 'DONE'], k.status), k.number;
