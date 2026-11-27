insert into comments (post_id, user_id, parent_id, body) values (:post_id, :user_id, :parent_id, :body) returning id;
