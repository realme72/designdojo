select m.conversation_id,
       coalesce(c.name, (select u.name from members o join users u on u.id = o.user_id
                         where o.conversation_id = m.conversation_id and o.user_id <> m.user_id)) as title,
       last.body as last_message,
       (select count(*) from messages x
        where x.conversation_id = m.conversation_id and x.id > m.last_read_id and x.sender_id <> m.user_id) as unread
from members m
join conversations c on c.id = m.conversation_id
join lateral (select body, id from messages x where x.conversation_id = m.conversation_id
              order by x.id desc limit 1) last on true
where m.user_id = :user_id
order by last.id desc;
