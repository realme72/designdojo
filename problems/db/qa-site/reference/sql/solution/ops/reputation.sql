select
  coalesce((select sum(case when v.value = 1 then 5 else -2 end)
            from question_votes v join questions q on q.id = v.question_id where q.user_id = :user_id), 0)
+ coalesce((select sum(case when v.value = 1 then 10 else -2 end)
            from answer_votes v join answers a on a.id = v.answer_id where a.user_id = :user_id), 0)
+ 15 * (select count(*) from questions q join answers a on a.id = q.accepted_answer_id where a.user_id = :user_id)
  as reputation;
