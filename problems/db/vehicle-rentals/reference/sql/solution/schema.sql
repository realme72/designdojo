create extension if not exists btree_gist;

create table vehicles (
  id         bigint generated always as identity primary key,
  plate      text not null unique,
  category   text not null check (category in ('HATCH', 'SEDAN', 'SUV')),
  daily_rate numeric(10, 2) not null check (daily_rate > 0)
);
create index vehicles_category_idx on vehicles (category, plate);

create table customers (id bigint generated always as identity primary key, licence text not null unique, name text not null);

create table rentals (
  id          bigint generated always as identity primary key,
  vehicle_id  bigint not null references vehicles (id),
  customer_id bigint not null references customers (id),
  from_day    date not null,
  to_day      date not null,
  status      text not null default 'BOOKED' check (status in ('BOOKED', 'RETURNED', 'CANCELLED')),
  km          int check (km >= 0),
  charge      numeric(12, 2),
  check (to_day > from_day),
  check ((status = 'RETURNED') = (charge is not null)),
  exclude using gist (vehicle_id with =, daterange(from_day, to_day) with &&) where (status <> 'CANCELLED')
);
create index rentals_customer_idx on rentals (customer_id);
