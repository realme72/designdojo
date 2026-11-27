create extension if not exists btree_gist;

create table screens (id bigint generated always as identity primary key, name text not null);

create table seats (
  id        bigint generated always as identity primary key,
  screen_id bigint not null references screens (id),
  row_label text not null,
  number    int not null check (number >= 1),
  label     text generated always as (row_label || number) stored,
  unique (screen_id, row_label, number),
  unique (screen_id, id)
);

create table shows (
  id        bigint generated always as identity primary key,
  screen_id bigint not null references screens (id),
  movie     text not null,
  starts_at timestamptz not null,
  ends_at   timestamptz not null,
  check (ends_at > starts_at),
  unique (id, screen_id),
  exclude using gist (screen_id with =, tstzrange(starts_at, ends_at) with &&)
);
create index shows_movie_idx on shows (movie, starts_at);

create table bookings (
  id       bigint generated always as identity primary key,
  show_id  bigint not null references shows (id),
  customer text not null
);
create index bookings_show_idx on bookings (show_id);

create table booked_seats (
  booking_id bigint not null references bookings (id) on delete cascade,
  show_id    bigint not null,
  screen_id  bigint not null,
  seat_id    bigint not null,
  primary key (show_id, seat_id),                                          -- once per show
  foreign key (show_id, screen_id) references shows (id, screen_id),
  foreign key (screen_id, seat_id) references seats (screen_id, id)        -- seat of that screen
);
create index booked_seats_booking_idx on booked_seats (booking_id);
create index booked_seats_seat_idx on booked_seats (screen_id, seat_id);
