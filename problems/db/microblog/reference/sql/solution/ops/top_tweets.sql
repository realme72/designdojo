select t.id, u.handle as author,
       (select count(*) from retweets r where r.tweet_id = t.id)  as retweets,
       (select count(*) from tweets c where c.reply_to = t.id)    as replies
from tweets t
join users u on u.id = t.user_id
order by retweets desc, replies desc, t.id
limit :n;
