create table customers (
  id         bigint generated always as identity primary key,
  email      text not null,
  name       text not null,
  created_at timestamptz not null default now()
);
-- case-insensitive uniqueness
create unique index customers_email_lower_key on customers (lower(email));

create table products (
  id    bigint generated always as identity primary key,
  sku   text not null unique,
  name  text not null,
  price numeric(10, 2) not null check (price >= 0),
  stock int not null check (stock >= 0)
);

create table orders (
  id          bigint generated always as identity primary key,
  customer_id bigint not null references customers (id),
  status      text not null default 'PLACED'
              check (status in ('PLACED', 'PAID', 'SHIPPED', 'CANCELLED')),
  created_at  timestamptz not null default now()
);
create index orders_customer_id_idx on orders (customer_id);

create table order_items (
  order_id   bigint not null references orders (id) on delete cascade,
  product_id bigint not null references products (id),
  quantity   int not null check (quantity > 0),
  unit_price numeric(10, 2) not null check (unit_price >= 0),  -- price at order time
  primary key (order_id, product_id)
);
create index order_items_product_id_idx on order_items (product_id);
