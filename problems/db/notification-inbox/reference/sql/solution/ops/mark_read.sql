update notifications set read_at = coalesce(read_at, now()) where id = :notification_id;
