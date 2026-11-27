insert into votes (user_id, post_id, value) values (:user_id, :post_id, :value)
on conflict (post_id, user_id) do update set value = excluded.value;
