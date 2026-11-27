select t.driver_id, round(avg((t.status = 'cancelled_by_driver')::int), 2) as cancel_rate
from trips t
join users c on c.id = t.client_id and not c.banned
join users d on d.id = t.driver_id and not d.banned
group by t.driver_id having count(*) >= :min_trips
order by cancel_rate desc, t.driver_id;
