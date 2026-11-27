select h as hour
from generate_series(date_trunc('hour', :from::timestamptz), :to::timestamptz - interval '1 hour', interval '1 hour') h
where h >= :from and not exists (select 1 from readings r where r.sensor_id = :sensor_id and r.ts = h)
order by h;
