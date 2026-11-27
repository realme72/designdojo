select distinct on (s.name) s.name as sensor, r.ts as peak_hour, r.value as peak
from readings r join sensors s on s.id = r.sensor_id
where r.ts >= (:day::date)::timestamp at time zone 'UTC' and r.ts < (:day::date + 1)::timestamp at time zone 'UTC'
order by s.name, r.value desc, r.ts;
