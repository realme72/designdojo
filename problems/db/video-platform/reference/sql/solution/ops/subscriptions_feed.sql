select v.title, c.handle as channel
from subscriptions s
join videos v on v.channel_id = s.channel_id and v.visibility = 'PUBLIC'
join channels c on c.id = v.channel_id
where s.user_id = :user_id
order by v.uploaded_at desc, v.title
limit :n;
