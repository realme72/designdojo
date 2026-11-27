select t.title, count(p.id) as plays
from track_artists ta
join tracks t on t.id = ta.track_id
left join plays p on p.track_id = t.id and p.seconds >= 30
where ta.artist_id = :artist_id
group by t.id, t.title
order by plays desc, t.title
limit :n;
