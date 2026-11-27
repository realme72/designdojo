select resource, action from user_permissions where user_id = :user_id order by resource, action;
