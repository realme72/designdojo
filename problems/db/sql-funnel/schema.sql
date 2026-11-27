create table events (
  user_id    int not null,
  event_type text not null check (event_type in ('VIEW', 'CART', 'PURCHASE')),
  at         timestamptz not null
);
