select coalesce(sum(amount), 0) from transactions where account_id = :account_id and posted_at <= :at;
