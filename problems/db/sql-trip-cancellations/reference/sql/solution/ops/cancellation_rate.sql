select t.request_at as day, round(avg((t.status <> 'completed')::int), 2) as rate
from trips t
join users c on c.id = t.client_id and not c.banned
join users d on d.id = t.driver_id and not d.banned
where t.request_at between :from_day and :to_day
group by t.request_at order by t.request_at;
