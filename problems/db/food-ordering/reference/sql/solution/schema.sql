create table restaurants (id bigint generated always as identity primary key, name text not null);
create table customers (id bigint generated always as identity primary key, name text not null);
create table agents (id bigint generated always as identity primary key, name text not null);

create table menu_items (
  id            bigint generated always as identity primary key,
  restaurant_id bigint not null references restaurants (id),
  name          text not null,
  price         numeric(10, 2) not null check (price >= 0),
  available     boolean not null default true,
  unique (restaurant_id, id)
);

create table orders (
  id            bigint generated always as identity primary key,
  customer_id   bigint not null references customers (id),
  restaurant_id bigint not null references restaurants (id),
  agent_id      bigint references agents (id),
  status        text not null default 'PLACED'
                check (status in ('PLACED', 'PREPARING', 'PICKED_UP', 'DELIVERED', 'CANCELLED')),
  total         numeric(10, 2) not null default 0 check (total >= 0),
  unique (id, restaurant_id)
);
create index orders_customer_idx on orders (customer_id);
create index orders_restaurant_idx on orders (restaurant_id);
create unique index orders_one_active_per_agent on orders (agent_id)
  where status in ('PLACED', 'PREPARING', 'PICKED_UP');

create table order_items (
  order_id      bigint not null,
  restaurant_id bigint not null,
  item_id       bigint not null,
  qty           int not null check (qty >= 1),
  unit_price    numeric(10, 2) not null check (unit_price >= 0),
  primary key (order_id, item_id),
  foreign key (order_id, restaurant_id) references orders (id, restaurant_id) on delete cascade,
  foreign key (restaurant_id, item_id) references menu_items (restaurant_id, id)   -- same restaurant
);
create index order_items_item_idx on order_items (restaurant_id, item_id);

create table transitions (from_status text, to_status text, primary key (from_status, to_status));
insert into transitions values ('PLACED', 'PREPARING'), ('PREPARING', 'PICKED_UP'),
  ('PICKED_UP', 'DELIVERED'), ('PLACED', 'CANCELLED');

create function check_transition() returns trigger language plpgsql as $$
begin
  if new.status <> old.status and not exists
     (select 1 from transitions where from_status = old.status and to_status = new.status) then
    raise exception 'illegal transition % -> %', old.status, new.status;
  end if;
  return new;
end $$;
create trigger orders_transition before update of status on orders for each row execute function check_transition();
