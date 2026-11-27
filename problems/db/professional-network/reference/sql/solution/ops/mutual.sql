select u.name
from user_links a join user_links b on b.other_id = a.other_id
join users u on u.id = a.other_id
where a.user_id = :a_id and b.user_id = :b_id
order by u.name;
