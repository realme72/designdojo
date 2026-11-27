select round(avg(extract(epoch from (d.at - s.created_at)) / 3600)::numeric, 1)
from shipments s join events d on d.shipment_id = s.id and d.status = 'DELIVERED'
where s.origin = :origin and s.destination = :destination;
