insert into posts (community_id, user_id, title, created_at) values (:community_id, :user_id, :title, :created_at) returning id;
