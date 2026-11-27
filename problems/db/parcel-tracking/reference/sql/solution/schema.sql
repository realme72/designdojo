create table statuses (status text primary key);
insert into statuses values ('CREATED'), ('PICKED_UP'), ('IN_TRANSIT'), ('OUT_FOR_DELIVERY'), ('DELIVERED');

create table transitions (
  from_status text references statuses (status),
  to_status   text references statuses (status),
  primary key (from_status, to_status)
);
create index transitions_to_idx on transitions (to_status);
insert into transitions values ('CREATED', 'PICKED_UP'), ('PICKED_UP', 'IN_TRANSIT'), ('IN_TRANSIT', 'IN_TRANSIT'),
  ('IN_TRANSIT', 'OUT_FOR_DELIVERY'), ('OUT_FOR_DELIVERY', 'DELIVERED'), ('OUT_FOR_DELIVERY', 'IN_TRANSIT');

create table shipments (
  id          bigint generated always as identity primary key,
  tracking_no text not null unique,
  origin      text not null,
  destination text not null,
  created_at  timestamptz not null
);
create index shipments_lane_idx on shipments (origin, destination);

create table events (
  id          bigint generated always as identity primary key,
  shipment_id bigint not null references shipments (id),
  status      text not null references statuses (status),
  location    text not null,
  at          timestamptz not null
);
create index events_shipment_time_idx on events (shipment_id, at, id);
create index events_status_idx on events (status);

create function check_scan() returns trigger language plpgsql as $$
declare prev events%rowtype;
begin
  select * into prev from events where shipment_id = new.shipment_id order by at desc, id desc limit 1;
  if prev.id is null then
    if new.status <> 'CREATED' then raise exception 'first event must be CREATED'; end if;
    return new;
  end if;
  if new.at < prev.at then raise exception 'scan earlier than the previous event'; end if;
  if not exists (select 1 from transitions where from_status = prev.status and to_status = new.status) then
    raise exception 'illegal transition % -> %', prev.status, new.status;
  end if;
  return new;
end $$;
create trigger events_check before insert on events for each row execute function check_scan();
create function reject_change() returns trigger language plpgsql as $$ begin raise exception 'events are append-only'; end $$;
create trigger events_append_only before update or delete on events for each row execute function reject_change();
