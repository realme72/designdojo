insert into question_votes (user_id, question_id, value) values (:user_id, :question_id, :value)
on conflict (question_id, user_id) do update set value = excluded.value;
