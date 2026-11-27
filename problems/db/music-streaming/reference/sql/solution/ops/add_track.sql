with t as (
  insert into tracks (title, duration_s)
  select :title, :duration_s where cardinality(:artist_ids::int[]) > 0
  union all
  select :title, null where coalesce(cardinality(:artist_ids::int[]), 0) = 0   -- no artists: refuse
  returning id
),
credits as (
  insert into track_artists (track_id, artist_id, position)
  select t.id, a.artist_id, a.pos from t, unnest(:artist_ids::int[]) with ordinality as a(artist_id, pos)
)
select id from t;
