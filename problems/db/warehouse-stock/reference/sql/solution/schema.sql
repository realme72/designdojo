create table products (id bigint generated always as identity primary key, sku text not null unique);
create table warehouses (id bigint generated always as identity primary key, code text not null unique);

create table stock (
  warehouse_id bigint not null references warehouses (id),
  product_id   bigint not null references products (id),
  qty          int not null check (qty >= 0),
  primary key (warehouse_id, product_id)
);
create index stock_product_idx on stock (product_id);

create table movements (
  id           bigint generated always as identity primary key,
  warehouse_id bigint not null references warehouses (id),
  product_id   bigint not null references products (id),
  change       int not null check (change <> 0),
  reason       text not null check (reason in ('RECEIVE', 'SHIP', 'TRANSFER'))
);
create index movements_product_idx on movements (product_id, id);
create index movements_warehouse_idx on movements (warehouse_id);
