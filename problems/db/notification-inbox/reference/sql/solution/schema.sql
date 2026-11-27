create table users (id bigint generated always as identity primary key, name text not null);

create table notification_types (name text primary key);
insert into notification_types values ('LIKE'), ('COMMENT'), ('FOLLOW'), ('SYSTEM');

create table mutes (
  user_id bigint not null references users (id),
  type    text not null references notification_types (name),
  primary key (user_id, type)
);

create table notifications (
  id              bigint generated always as identity primary key,
  user_id         bigint not null references users (id),
  type            text not null references notification_types (name),
  text            text not null,
  idempotency_key text not null,
  created_at      timestamptz not null,
  read_at         timestamptz,
  unique (user_id, idempotency_key)
);
create index notifications_user_time_idx on notifications (user_id, created_at desc, id desc);
create index notifications_unread_idx on notifications (user_id) where read_at is null;
create index notifications_type_idx on notifications (type);
create index mutes_type_idx on mutes (type);
