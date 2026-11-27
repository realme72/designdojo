update issues set assignee_id = :user_id where id = (select id from issue_keys where issue_key = :issue_key);
