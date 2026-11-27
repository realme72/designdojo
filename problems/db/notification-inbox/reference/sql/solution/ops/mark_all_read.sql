update notifications set read_at = now() where user_id = :user_id and read_at is null;
