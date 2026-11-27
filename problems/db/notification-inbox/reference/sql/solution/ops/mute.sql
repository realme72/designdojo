insert into mutes (user_id, type) values (:user_id, :type) on conflict do nothing;
