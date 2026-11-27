# Trip Cancellation Rate

> **Interview questions** (tab next to Problem): start there.

Schema given: `users(id, role, banned)` and `trips(id, client_id, driver_id, status, request_at)`.

The **cancellation rate** of a day = trips cancelled (by client or driver) ÷ all trips that day,
counting only trips where **neither the client nor the driver is banned**. Round to 2 decimals.

| Query | Returns |
|---|---|
| `cancellation_rate(:from_day, :to_day)` | rows `day`, `rate`: days in the inclusive range that have at least one counted trip, by day |
| `worst_drivers(:min_trips)` | rows `driver_id`, `cancel_rate`: unbanned drivers with at least `:min_trips` counted trips, by their own driver-cancellation rate desc then id; 2 decimals |
