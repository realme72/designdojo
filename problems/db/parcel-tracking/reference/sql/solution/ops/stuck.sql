select s.tracking_no, l.status
from shipments s
join lateral (select status, at from events e where e.shipment_id = s.id order by e.at desc, e.id desc limit 1) l on true
where l.status <> 'DELIVERED' and l.at < :at::timestamptz - make_interval(hours => :hours)
order by s.tracking_no;
