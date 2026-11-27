select d.name as driver, count(t.id) as trips, coalesce(sum(t.fare), 0) as earned
from drivers d
left join trips t on t.driver_id = d.id and t.status = 'COMPLETED'
     and t.requested_at >= :from and t.requested_at < :to
group by d.id, d.name
order by earned desc, d.name;
