insert into answers (question_id, user_id, body) values (:question_id, :user_id, :body) returning id;
