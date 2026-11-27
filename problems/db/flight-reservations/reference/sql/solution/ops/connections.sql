select f1.code as first, f2.code as second,
       (extract(epoch from f2.departs_at - f1.arrives_at) / 60)::int as layover_min
from flights f1
join flights f2 on f2.origin = f1.destination
 and f2.departs_at between f1.arrives_at + interval '45 minutes' and f1.arrives_at + interval '6 hours'
where f1.origin = :origin and f2.destination = :destination
order by f2.arrives_at, f1.code, f2.code;
