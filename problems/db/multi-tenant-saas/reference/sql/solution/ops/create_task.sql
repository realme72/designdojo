insert into tasks (tenant_id, project_id, title, assignee_id) values (:tenant_id, :project_id, :title, :assignee_id) returning id;
