# Sensor Time Series

> **Interview questions** (tab next to Problem): start there.

Schema given: `sensors(id, name)` and `readings(sensor_id, ts, value)`. Sensors should report
**every hour on the hour** (UTC), but some readings are missing.

| Query | Returns |
|---|---|
| `missing_hours(:sensor_id, :from, :to)` | rows `hour`: expected hours in `[from, to)` with no reading, in order |
| `rolling_avg(:sensor_id)` | rows `ts`, `value`, `avg3`: each reading with the average of it and the **two previous readings** (fewer at the start), 2 decimals |
| `outages(:sensor_id, :from, :to)` | rows `started`, `ended`, `hours`: runs of consecutive missing hours in `[from, to)`; `ended` is the first hour after the run |
| `hourly_max(:day)` | rows `sensor`, `peak_hour`, `peak`: per sensor with readings that UTC day, the hour of its highest value (ties: earliest), by sensor name |
