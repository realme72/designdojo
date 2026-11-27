with s as (
  insert into shipments (tracking_no, origin, destination, created_at)
  values (:tracking_no, :origin, :destination, :at) returning id, origin, created_at
),
e as (insert into events (shipment_id, status, location, at) select id, 'CREATED', origin, created_at from s)
select id from s;
