create table users (
  id       bigint generated always as identity primary key,
  username text not null check (length(username) > 0)
);
create unique index users_username_lower_key on users (lower(username));

create table follows (
  follower_id bigint not null references users (id),
  followee_id bigint not null references users (id),
  primary key (follower_id, followee_id),
  check (follower_id <> followee_id)
);
create index follows_followee_idx on follows (followee_id, follower_id);

create table posts (
  id        bigint generated always as identity primary key,
  user_id   bigint not null references users (id),
  caption   text not null default '',
  posted_at timestamptz not null
);
create index posts_user_time_idx on posts (user_id, posted_at desc);

create table likes (
  user_id bigint not null references users (id),
  post_id bigint not null references posts (id) on delete cascade,
  primary key (post_id, user_id)
);
create index likes_user_idx on likes (user_id);

create table comments (
  id      bigint generated always as identity primary key,
  user_id bigint not null references users (id),
  post_id bigint not null references posts (id) on delete cascade,
  body    text not null check (length(trim(body)) > 0)
);
create index comments_post_idx on comments (post_id);
create index comments_user_idx on comments (user_id);
