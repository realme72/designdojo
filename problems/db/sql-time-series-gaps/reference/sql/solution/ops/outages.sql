with missing as (
  select h from generate_series(:from::timestamptz, :to::timestamptz - interval '1 hour', interval '1 hour') h
  where not exists (select 1 from readings r where r.sensor_id = :sensor_id and r.ts = h)
),
islands as (select h, h - (row_number() over (order by h)) * interval '1 hour' as grp from missing)
select min(h) as started, max(h) + interval '1 hour' as ended, count(*) as hours
from islands group by grp order by started;
