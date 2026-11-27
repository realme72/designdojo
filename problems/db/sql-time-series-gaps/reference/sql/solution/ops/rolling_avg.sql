select ts, value, round(avg(value) over (order by ts rows between 2 preceding and current row), 2) as avg3
from readings where sensor_id = :sensor_id order by ts;
