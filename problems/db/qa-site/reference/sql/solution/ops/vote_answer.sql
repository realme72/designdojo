insert into answer_votes (user_id, answer_id, value) values (:user_id, :answer_id, :value)
on conflict (answer_id, user_id) do update set value = excluded.value;
