create table users (id bigint generated always as identity primary key, username text not null unique);
create table communities (id bigint generated always as identity primary key, name text not null unique);

create table posts (
  id           bigint generated always as identity primary key,
  community_id bigint not null references communities (id),
  user_id      bigint not null references users (id),
  title        text not null check (length(title) > 0),
  created_at   timestamptz not null
);
create index posts_community_idx on posts (community_id);
create index posts_user_idx on posts (user_id);

create table votes (
  user_id bigint not null references users (id),
  post_id bigint not null references posts (id) on delete cascade,
  value   smallint not null check (value in (-1, 1)),
  primary key (post_id, user_id)
);
create index votes_user_idx on votes (user_id);

create table comments (
  id        bigint generated always as identity primary key,
  post_id   bigint not null references posts (id) on delete cascade,
  user_id   bigint not null references users (id),
  parent_id bigint,
  body      text not null check (length(trim(body)) > 0),
  unique (post_id, id),
  -- a reply must be on the same post as its parent
  foreign key (post_id, parent_id) references comments (post_id, id)
);
create index comments_parent_idx on comments (post_id, parent_id);
create index comments_user_idx on comments (user_id);
