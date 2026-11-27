select e.position, t.title,
       (select string_agg(a.name, ', ' order by ta.position)
        from track_artists ta join artists a on a.id = ta.artist_id where ta.track_id = t.id) as artists
from playlist_entries e join tracks t on t.id = e.track_id
where e.playlist_id = :playlist_id
order by e.position;
