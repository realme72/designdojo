insert into comments (user_id, post_id, body) values (:user_id, :post_id, :body) returning id;
