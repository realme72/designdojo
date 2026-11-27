select t.slug, t.plan,
       (select count(*) from users u where u.tenant_id = t.id) as users,
       (select count(*) from projects p where p.tenant_id = t.id) as projects,
       (select count(*) from tasks k where k.tenant_id = t.id) as tasks
from tenants t order by t.slug;
