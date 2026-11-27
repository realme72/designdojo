insert into posts (user_id, caption, posted_at) values (:user_id, :caption, :posted_at) returning id;
