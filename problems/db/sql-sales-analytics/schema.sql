create table customers (id int primary key, name text not null);
create table orders (
  id          int primary key,
  customer_id int not null references customers (id),
  ordered_at  timestamptz not null,
  amount      numeric(10, 2) not null check (amount >= 0)
);
