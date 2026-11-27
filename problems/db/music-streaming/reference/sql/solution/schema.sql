create table artists (id bigint generated always as identity primary key, name text not null unique);
create table users (id bigint generated always as identity primary key, name text not null);

create table tracks (
  id         bigint generated always as identity primary key,
  title      text not null,
  duration_s int not null check (duration_s > 0)
);

create table track_artists (
  track_id  bigint not null references tracks (id) on delete cascade,
  artist_id bigint not null references artists (id),
  position  int not null check (position >= 1),
  primary key (track_id, artist_id),
  unique (track_id, position)
);
create index track_artists_artist_idx on track_artists (artist_id);

create table playlists (
  id      bigint generated always as identity primary key,
  user_id bigint not null references users (id),
  name    text not null
);
create index playlists_user_idx on playlists (user_id);

create table playlist_entries (
  id          bigint generated always as identity primary key,  -- a track may appear twice
  playlist_id bigint not null references playlists (id) on delete cascade,
  track_id    bigint not null references tracks (id),
  position    int not null check (position >= 1),
  constraint playlist_position_unique unique (playlist_id, position) deferrable initially immediate
);
create index playlist_entries_track_idx on playlist_entries (track_id);

create table plays (
  id        bigint generated always as identity primary key,
  user_id   bigint not null references users (id),
  track_id  bigint not null references tracks (id),
  played_at timestamptz not null,
  seconds   int not null check (seconds >= 0)
);
create index plays_track_idx on plays (track_id);
create index plays_user_time_idx on plays (user_id, played_at);

create function play_within_duration() returns trigger language plpgsql as $$
begin
  if new.seconds > (select duration_s from tracks where id = new.track_id) then
    raise exception 'listened longer than the track';
  end if;
  return new;
end $$;
create trigger plays_within_duration before insert on plays for each row execute function play_within_duration();
