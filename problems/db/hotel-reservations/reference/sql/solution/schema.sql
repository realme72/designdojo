create extension if not exists btree_gist;  -- lets a gist index compare room_id with =

create table room_types (
  id           bigint generated always as identity primary key,
  name         text not null unique,
  nightly_rate numeric(10, 2) not null check (nightly_rate >= 0)
);

create table rooms (
  id           bigint generated always as identity primary key,
  number       text not null unique,
  room_type_id bigint not null references room_types (id)
);
create index rooms_room_type_id_idx on rooms (room_type_id);

create table guests (
  id    bigint generated always as identity primary key,
  email text not null unique,
  name  text not null
);

create table bookings (
  id        bigint generated always as identity primary key,
  room_id   bigint not null references rooms (id),
  guest_id  bigint not null references guests (id),
  check_in  date not null,
  check_out date not null,
  total     numeric(12, 2) not null check (total >= 0),   -- price fixed at booking time
  status    text not null default 'CONFIRMED' check (status in ('CONFIRMED', 'CANCELLED')),
  check (check_out > check_in),
  -- race-free: two confirmed stays of one room can't overlap ([) ranges: back-to-back is fine)
  exclude using gist (room_id with =, daterange(check_in, check_out) with &&) where (status = 'CONFIRMED')
);
create index bookings_guest_id_idx on bookings (guest_id);
