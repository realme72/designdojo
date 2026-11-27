insert into playlist_entries (playlist_id, track_id, position)
select :playlist_id, :track_id, coalesce(max(position), 0) + 1 from playlist_entries where playlist_id = :playlist_id;
