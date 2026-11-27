create table links (
  id         bigint generated always as identity primary key,
  code       text not null unique,
  url        text not null check (url ~ '^https?://'),
  owner      text not null,
  created_at timestamptz not null,
  expires_at timestamptz,
  check (expires_at is null or expires_at > created_at)
);
create index links_owner_idx on links (owner);

create table clicks (
  id         bigint generated always as identity primary key,
  link_id    bigint not null references links (id),
  clicked_at timestamptz not null,
  country    text not null
);
create index clicks_link_time_idx on clicks (link_id, clicked_at);
