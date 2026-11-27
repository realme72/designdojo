select p.name as project, t.title from tasks t
join projects p on p.tenant_id = t.tenant_id and p.id = t.project_id
where t.tenant_id = :tenant_id and t.assignee_id = :user_id order by p.name, t.title;
