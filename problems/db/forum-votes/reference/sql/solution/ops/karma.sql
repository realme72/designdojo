select coalesce(sum(v.value), 0) as karma
from posts p join votes v on v.post_id = p.id
where p.user_id = :user_id;
