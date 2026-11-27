create table users (
  id     int primary key,
  role   text not null check (role in ('client', 'driver')),
  banned boolean not null default false
);
create table trips (
  id         int primary key,
  client_id  int not null references users (id),
  driver_id  int not null references users (id),
  status     text not null check (status in ('completed', 'cancelled_by_driver', 'cancelled_by_client')),
  request_at date not null
);
