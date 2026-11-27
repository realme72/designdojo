create table vehicle_classes (
  class  text primary key,
  base   numeric(8, 2) not null check (base >= 0),
  per_km numeric(8, 2) not null check (per_km >= 0)
);
insert into vehicle_classes values ('MINI', 50, 10), ('SEDAN', 80, 14), ('SUV', 120, 20);

create table riders (id bigint generated always as identity primary key, name text not null);

create table drivers (
  id     bigint generated always as identity primary key,
  name   text not null,
  class  text not null references vehicle_classes (class),
  online boolean not null default false,
  lat    numeric(9, 6) check (lat between -90 and 90),
  lng    numeric(9, 6) check (lng between -180 and 180)
);
create index drivers_available_idx on drivers (class) where online;

create table trips (
  id           bigint generated always as identity primary key,
  rider_id     bigint not null references riders (id),
  driver_id    bigint not null references drivers (id),
  class        text not null references vehicle_classes (class),
  pickup_lat   numeric(9, 6) not null,
  pickup_lng   numeric(9, 6) not null,
  requested_at timestamptz not null,
  status       text not null default 'ACCEPTED' check (status in ('ACCEPTED', 'COMPLETED', 'CANCELLED')),
  km           numeric(8, 2) check (km >= 0),
  fare         numeric(10, 2),
  check ((status = 'COMPLETED') = (fare is not null))
);
create unique index trips_one_active_driver on trips (driver_id) where status = 'ACCEPTED';
create unique index trips_one_active_rider on trips (rider_id) where status = 'ACCEPTED';
create index trips_requested_idx on trips (requested_at);
create index trips_class_idx on trips (class);
