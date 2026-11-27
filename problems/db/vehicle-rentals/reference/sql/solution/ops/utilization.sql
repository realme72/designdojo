-- careful: for vehicles without rentals the LEFT JOIN gives daterange(NULL, NULL), which is
-- UNBOUNDED - intersecting it with the window would count the whole window. Count matches only.
select v.plate,
       coalesce(sum(upper(daterange(r.from_day, r.to_day) * daterange(:from_day, :to_day))
                  - lower(daterange(r.from_day, r.to_day) * daterange(:from_day, :to_day)))
                filter (where r.id is not null), 0) as days
from vehicles v
left join rentals r on r.vehicle_id = v.id and r.status <> 'CANCELLED'
     and daterange(r.from_day, r.to_day) && daterange(:from_day, :to_day)
group by v.id, v.plate order by v.plate;
