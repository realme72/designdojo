select count(*) from notifications where user_id = :user_id and read_at is null;
