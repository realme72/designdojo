create table users (id bigint generated always as identity primary key, name text not null);

create table items (
  id             bigint generated always as identity primary key,
  seller_id      bigint not null references users (id),
  title          text not null,
  start_price    numeric(12, 2) not null check (start_price > 0),
  ends_at        timestamptz not null,
  current_price  numeric(12, 2),
  current_leader bigint references users (id),
  check ((current_price is null) = (current_leader is null))
);
create index items_seller_idx on items (seller_id);
create index items_leader_idx on items (current_leader);

create table bids (
  id        bigint generated always as identity primary key,
  item_id   bigint not null references items (id),
  bidder_id bigint not null references users (id),
  amount    numeric(12, 2) not null check (amount > 0),
  placed_at timestamptz not null
);
create index bids_item_idx on bids (item_id, amount desc);
create index bids_bidder_idx on bids (bidder_id);

create function reject_change() returns trigger language plpgsql as $$
begin raise exception 'bids are immutable'; end $$;
create trigger bids_immutable before update or delete on bids for each row execute function reject_change();
