create table users (id bigint generated always as identity primary key, name text not null);

create table requests (
  id      bigint generated always as identity primary key,
  from_id bigint not null references users (id),
  to_id   bigint not null references users (id),
  status  text not null default 'PENDING' check (status in ('PENDING', 'ACCEPTED', 'DECLINED')),
  check (from_id <> to_id)
);
-- one pending request per unordered pair, whoever sent it
create unique index requests_one_pending on requests (least(from_id, to_id), greatest(from_id, to_id)) where status = 'PENDING';
create index requests_to_idx on requests (to_id);
create index requests_from_idx on requests (from_id);

create table connections (
  user_low  bigint not null references users (id),
  user_high bigint not null references users (id),
  primary key (user_low, user_high),
  check (user_low < user_high)
);
create index connections_high_idx on connections (user_high, user_low);

create view user_links as
  select user_low as user_id, user_high as other_id from connections
  union all
  select user_high, user_low from connections;
