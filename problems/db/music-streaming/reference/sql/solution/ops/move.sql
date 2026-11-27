set constraints playlist_position_unique deferred;
update playlist_entries
set position = case
  when position = :from_pos then :to_pos
  when :from_pos < :to_pos then position - 1   -- moving down: entries in between shift up
  else position + 1                            -- moving up: entries in between shift down
end
where playlist_id = :playlist_id
  and position between least(:from_pos::int, :to_pos::int) and greatest(:from_pos::int, :to_pos::int);
