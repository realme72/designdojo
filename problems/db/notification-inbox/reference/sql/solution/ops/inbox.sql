select type, text, read_at is not null as read
from notifications where user_id = :user_id
order by created_at desc, id desc
limit :n;
