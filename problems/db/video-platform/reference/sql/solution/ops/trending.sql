select v.title, c.handle as channel, count(*) as views
from views w
join videos v on v.id = w.video_id and v.visibility = 'PUBLIC'
join channels c on c.id = v.channel_id
where w.viewed_at >= :since
group by v.id, v.title, c.handle
order by views desc, v.title
limit :n;
