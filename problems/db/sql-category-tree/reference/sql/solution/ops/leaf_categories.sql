select c.name from categories c where not exists (select 1 from categories k where k.parent_id = c.id) order by c.name;
