create extension if not exists btree_gist;

create table dining_tables (
  id    bigint generated always as identity primary key,
  label text not null unique,
  seats int not null check (seats between 2 and 12)
);

create table reservations (
  id         bigint generated always as identity primary key,
  table_id   bigint not null references dining_tables (id),
  guest      text not null,
  party_size int not null check (party_size >= 1),
  starts_at  timestamptz not null,
  ends_at    timestamptz not null,
  cancelled  boolean not null default false,
  check (ends_at = starts_at + interval '2 hours'),
  exclude using gist (table_id with =, tstzrange(starts_at, ends_at) with &&) where (not cancelled)
);
create index reservations_start_idx on reservations (starts_at);
