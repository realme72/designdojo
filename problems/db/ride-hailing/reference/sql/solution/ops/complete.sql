update trips t set status = 'COMPLETED', km = :km, fare = c.base + c.per_km * :km
from vehicle_classes c
where c.class = t.class and t.id = :trip_id and t.status = 'ACCEPTED'
returning t.fare;
