create table spot_types (type text primary key, hourly_rate numeric(8, 2) not null check (hourly_rate >= 0));
insert into spot_types values ('COMPACT', 20), ('LARGE', 40), ('EV', 30);

create table lots (id bigint generated always as identity primary key, name text not null);

create table spots (
  id     bigint generated always as identity primary key,
  lot_id bigint not null references lots (id),
  number int not null check (number >= 1),
  type   text not null references spot_types (type),
  unique (lot_id, number)
);
create index spots_lot_type_idx on spots (lot_id, type, number);
create index spots_type_idx on spots (type);

create table vehicles (id bigint generated always as identity primary key, plate text not null unique);

create table sessions (
  id         bigint generated always as identity primary key,
  spot_id    bigint not null references spots (id),
  vehicle_id bigint not null references vehicles (id),
  entered_at timestamptz not null,
  exited_at  timestamptz,
  fee        numeric(10, 2),
  check (exited_at is null or exited_at >= entered_at),
  check ((exited_at is null) = (fee is null))
);
create unique index sessions_open_per_spot on sessions (spot_id) where exited_at is null;
create unique index sessions_open_per_vehicle on sessions (vehicle_id) where exited_at is null;
