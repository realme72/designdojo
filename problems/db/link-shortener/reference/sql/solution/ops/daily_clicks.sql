select d::date as day, count(c.id) as clicks
from generate_series(:from_day::date, :to_day::date, interval '1 day') d
left join links l on l.code = :code
left join clicks c on c.link_id = l.id and (c.clicked_at at time zone 'UTC')::date = d::date
group by d order by d;
