select (select count(*) from subscriptions s where s.channel_id = c.id) as subscribers,
       (select count(*) from videos v where v.channel_id = c.id and v.visibility = 'PUBLIC') as videos,
       (select count(*) from views w join videos v on v.id = w.video_id where v.channel_id = c.id) as total_views
from channels c where c.id = :channel_id;
