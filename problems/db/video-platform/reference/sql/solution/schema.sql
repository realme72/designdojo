create table users (id bigint generated always as identity primary key, email text not null unique);

create table channels (
  id      bigint generated always as identity primary key,
  user_id bigint not null unique references users (id),   -- one channel per user
  handle  text not null unique
);

create table videos (
  id          bigint generated always as identity primary key,
  channel_id  bigint not null references channels (id),
  title       text not null,
  duration_s  int not null check (duration_s > 0),
  visibility  text not null check (visibility in ('PUBLIC', 'UNLISTED', 'PRIVATE')),
  uploaded_at timestamptz not null
);
create index videos_channel_idx on videos (channel_id, uploaded_at desc);

create table subscriptions (
  user_id    bigint not null references users (id),
  channel_id bigint not null references channels (id),
  primary key (user_id, channel_id)
);
create index subscriptions_channel_idx on subscriptions (channel_id);

create table views (
  id        bigint generated always as identity primary key,
  video_id  bigint not null references videos (id),
  user_id   bigint references users (id),   -- NULL = anonymous
  viewed_at timestamptz not null
);
create index views_video_time_idx on views (video_id, viewed_at);
create index views_user_idx on views (user_id);

create function no_self_subscribe() returns trigger language plpgsql as $$
begin
  if exists (select 1 from channels where id = new.channel_id and user_id = new.user_id) then
    raise exception 'cannot subscribe to your own channel';
  end if;
  return new;
end $$;
create trigger subscriptions_not_own before insert on subscriptions for each row execute function no_self_subscribe();
