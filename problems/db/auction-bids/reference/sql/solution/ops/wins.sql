select count(*) from items where current_leader = :user_id and ends_at <= :at;
