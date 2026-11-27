with counts as (
  select v.channel_id, v.title, count(w.id) as views
  from videos v left join views w on w.video_id = v.id
  group by v.id, v.channel_id, v.title
),
ranked as (
  select channel_id, title, views,
         row_number() over (partition by channel_id order by views desc, title) as rn
  from counts
)
select c.handle as channel, r.title, r.views
from ranked r join channels c on c.id = r.channel_id
where r.rn = 1
order by c.handle;
