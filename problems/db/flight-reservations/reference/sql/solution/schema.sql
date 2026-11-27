create table flights (
  id          bigint generated always as identity primary key,
  code        text not null unique,
  origin      char(3) not null,
  destination char(3) not null,
  departs_at  timestamptz not null,
  arrives_at  timestamptz not null,
  check (origin <> destination),
  check (arrives_at > departs_at)
);
create index flights_origin_time_idx on flights (origin, departs_at);
create index flights_destination_idx on flights (destination);

create table seats (
  id        bigint generated always as identity primary key,
  flight_id bigint not null references flights (id),
  seat_no   int not null check (seat_no >= 1),
  class     text not null check (class in ('ECONOMY', 'BUSINESS')),
  unique (flight_id, seat_no)
);
create index seats_flight_class_idx on seats (flight_id, class, seat_no);

create table reservations (
  id        bigint generated always as identity primary key,
  pnr       text not null unique,
  passenger text not null,
  seat_id   bigint not null unique references seats (id)   -- a seat is held at most once
);
