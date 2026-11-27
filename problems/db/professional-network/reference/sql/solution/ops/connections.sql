select u.name from user_links l join users u on u.id = l.other_id where l.user_id = :user_id order by u.name;
