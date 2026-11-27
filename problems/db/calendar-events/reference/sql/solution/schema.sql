create table users (id bigint generated always as identity primary key, name text not null);

create table events (
  id           bigint generated always as identity primary key,
  organizer_id bigint not null references users (id),
  title        text not null,
  starts_at    timestamptz not null,
  ends_at      timestamptz not null,
  check (ends_at > starts_at)
);
create index events_organizer_idx on events (organizer_id);
create index events_time_idx on events (starts_at, ends_at);

create table attendees (
  event_id bigint not null references events (id) on delete cascade,
  user_id  bigint not null references users (id),
  response text not null default 'INVITED' check (response in ('INVITED', 'ACCEPTED', 'DECLINED', 'TENTATIVE')),
  primary key (event_id, user_id)
);
create index attendees_user_idx on attendees (user_id);
