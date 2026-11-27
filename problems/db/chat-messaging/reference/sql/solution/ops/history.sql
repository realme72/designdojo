select x.id, u.name as sender, x.body
from messages x join users u on u.id = x.sender_id
where x.conversation_id = :conversation_id and (:before_id::bigint is null or x.id < :before_id)
order by x.id desc
limit :n;
