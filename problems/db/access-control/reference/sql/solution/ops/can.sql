select exists (select 1 from user_permissions where user_id = :user_id and resource = :resource and action = :action);
