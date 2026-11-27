create table products (id int primary key, name text not null, category text not null);
create table reviews (
  id         int primary key,
  product_id int not null references products (id),
  user_id    int not null,
  rating     int not null check (rating between 1 and 5),
  created_at timestamptz not null
);
