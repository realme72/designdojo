select u.name from user_permissions p join users u on u.id = p.user_id where p.resource = :resource and p.action = :action order by u.name;
